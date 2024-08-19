from rest_framework import status, viewsets
import imgkit
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Prefetch
from .models import CmOrders, CmOrderLine, CmOrderType, Discounts, OrderCancel
from rest_framework.permissions import IsAuthenticated
from products.models import ProductVariant, Uom
from users.models import CmEmployees, CmClients
from escpos.printer import Network
from jinja2 import Template
import weasyprint
from django.db import transaction
from django.db.models import Sum
# from django.conf import settings
from server.settings import socket_server_url
from pos.models import CmShifts, CmDays, CmTable, CmPos
from pos.serializers import CmShiftsSerializer
from kds.models import CmKdsOrder, CmKdsOrderline
from core.models import SiteSettings, DiscountType
from .serializers import CmOrdersSerializer, CmOrderLineSerializer, CmOrderTypeSerializer, DiscountsSerializer, OrderCancelSerializer
import logging
from .tasks import process_kitchen_display, process_kitchen_display_for_new_lines
import requests
import json

logger = logging.getLogger(__name__)

@permission_classes([IsAuthenticated])
class CmShiftsViewSet(viewsets.ModelViewSet):
    queryset = CmShifts.objects.all()
    serializer_class = CmShiftsSerializer

@permission_classes([IsAuthenticated])
class CmOrdersViewSet(viewsets.ModelViewSet):
    queryset = CmOrders.objects.all()
    serializer_class = CmOrdersSerializer


    @action(detail=False, methods=['get'])
    def suite_ordred(self, request):
        """
        Update the suite_ordred field for all order lines and related KDS order lines if suite_commande is True for a given order.
        """
        order_id = request.query_params.get('order_id', None)
        if order_id is None:
            return Response({"error": "order_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the order
            order = CmOrders.objects.get(id=order_id)

            # Get all order lines with suite_commande set to True
            orderlines = CmOrderLine.objects.filter(order=order, suite_commande=True)

            if not orderlines.exists():
                return Response({"message": "No order lines with suite_commande True found for this order."}, status=status.HTTP_404_NOT_FOUND)

            with transaction.atomic():
                # Update suite_ordred to True for all relevant order lines
                for orderline in orderlines:
                    orderline.suite_ordred = True
                    orderline.save()

                    # Update related KDS order lines
                    related_kds_orderlines = CmKdsOrderline.objects.filter(cm_pos_orderline=orderline)
                    for kds_orderline in related_kds_orderlines:
                        kds_orderline.suiteOrdred = True
                        kds_orderline.save()

            return Response({"message": "Order lines and related KDS order lines updated successfully."}, status=status.HTTP_200_OK)

        except CmOrders.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Failed to update suite_ordred for order: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        order_data = request.data
        print(order_data)
        orderlines_data = order_data.pop('orderlines')
        try:
            with transaction.atomic():
                # Fetch related instances using IDs
                related_fields = {
                    'cm_waiter': CmEmployees,
                    'cm_shift': CmShifts,
                    'cm_table': CmTable,
                    'delivery_guy': CmEmployees,
                    'client': CmClients,
                    'cm_order_type': CmOrderType,
                    'created_by': CmEmployees,
                    'updated_by': CmEmployees,
                }

                def get_instance(model, data):
                    if isinstance(data, dict):
                        return model.objects.filter(id=data.get('id')).first()
                    elif isinstance(data, int):
                        return model.objects.filter(id=data).first()
                    return None

                fetched_data = {key: get_instance(model, order_data.get(key)) for key, model in related_fields.items()}

                # Validate all fetched data
                # for key, value in fetched_data.items():
                #     if not value:
                #         return Response({"error": f"{key} not found."}, status=status.HTTP_400_BAD_REQUEST)

                # Log the retrieved objects
                logger.info(f"Fetched related data: {fetched_data}")

                # Create the order
                order = CmOrders.objects.create(
                    cm_waiter=fetched_data['cm_waiter'],
                    cm_shift=fetched_data['cm_shift'],
                    cm_table=fetched_data['cm_table'],
                    delivery_guy=fetched_data['delivery_guy'],
                    client=fetched_data['client'],
                    customer_count=order_data['customer_count'],
                    one_time=order_data['one_time'],
                    status="New",
                    total_amount=order_data["total_amount"],
                    cm_order_type=fetched_data['cm_order_type'],
                    created_by=fetched_data['created_by'],
                    updated_by=fetched_data['updated_by'],
                )

                # Prepare order lines for bulk create
                order_lines = [
                    CmOrderLine(
                        order=order,
                        price=ol_data['price'],
                        product_variant=ProductVariant.objects.get(id=ol_data['product_variant']['id']),
                        uom=Uom.objects.get(id=ol_data['uom']['id']),
                        customer_index=ol_data['customer_index'],
                        notes=ol_data['notes'],
                        qty=ol_data['qty'],
                        suite_commande=ol_data['suite_commande'],
                        cm_order_type=CmOrderType.objects.get(id=ol_data['cm_order_type']['id']),
                        suite_ordred=ol_data['suite_ordred'],
                        is_paid=ol_data['is_paid'],
                        is_ordred=True,
                    )
                    for ol_data in orderlines_data
                ]

                # Bulk create order lines
                created_orderlines = CmOrderLine.objects.bulk_create(order_lines)

                # Handle many-to-many relationships
                self._update_orderline_relationships(orderlines_data, created_orderlines)

                # Trigger asynchronous processing for kitchen display and KDS orders
                process_kitchen_display(order.id)

                # Serialize the order object
                order_serializer = self.get_serializer(order)
                return Response(order_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Order creation failed: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()  # Get the order instance
        order_data = request.data
        new_orderlines_data = order_data.pop('orderlines', [])

        try:
            with transaction.atomic():
                # Update the order fields if provided
                for field in ['status', 'customer_count', 'one_time','total_amount']:
                    if field in order_data:
                        setattr(order, field, order_data[field])
                order.save()

                # Prepare to store new order lines
                new_order_lines = []

                # Add new order lines
                for ol_data in new_orderlines_data:
                    new_order_line = CmOrderLine(
                        order=order,
                        price=ol_data['price'],
                        product_variant=ProductVariant.objects.get(id=ol_data['product_variant']['id']),
                        uom=Uom.objects.get(id=ol_data['uom']['id']),
                        customer_index=ol_data['customer_index'],
                        notes=ol_data['notes'],
                        qty=ol_data['qty'],
                        suite_commande=ol_data['suite_commande'],
                        cm_order_type=CmOrderType.objects.get(id=ol_data['cm_order_type']['id']),
                        suite_ordred=ol_data['suite_ordred'],
                        is_paid=ol_data['is_paid'],
                        is_ordred=True,
                    )
                    new_order_lines.append(new_order_line)

                # Bulk create new order lines
                CmOrderLine.objects.bulk_create(new_order_lines)

                # Handle many-to-many relationships
                self._update_orderline_relationships(new_orderlines_data, new_order_lines)

                # Send only new order lines to the KDS
                if new_order_lines:
                    process_kitchen_display_for_new_lines(order.id, new_order_lines)

            # Serialize the updated order
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Order update failed: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _update_orderline_relationships(self, orderlines_data, orderlines):
        for orderline_data, orderline in zip(orderlines_data, orderlines):
            
            combo_prod_ids = [pv['id'] for pv in orderline_data['combo_prods']]
            combo_supp_ids = [pv['id'] for pv in orderline_data['combo_supps']]

            orderline.combo_prods.set(combo_prod_ids)
            orderline.combo_supps.set(combo_supp_ids)


    @action(detail=True, methods=['post'])
    def action_cashdraw(self, request, pk=None):
        cm_pos_id = request.data.get('cm_pos_id')
        if not cm_pos_id:
            return Response({"error": "cm_pos_id are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cm_pos = CmPos.objects.get(id=cm_pos_id)
            ip_address = cm_pos.printer_ip
        except CmPos.DoesNotExist:
            return Response({"error": "CmPos not found"}, status=status.HTTP_404_NOT_FOUND)


        printer_port = 9100
        printer = Network(host=ip_address, port=9100)
        open_drawer_command = b'\x1b\x70\x00\x19\xfa'
        printer._raw(open_drawer_command)
        printer.close()
        return Response({"message": "cashdraw job successfully"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def print_ticket(self, request, pk=None):
        try:
            # Extract order_id and cm_pos from the request data
            order_id = request.data.get('order_id')
            cm_pos_id = request.data.get('cm_pos')
            orderlines = request.data.get('orderlines', None)

            if not order_id or not cm_pos_id:
                return Response({"error": "order_id and cm_pos are required."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the order and CmPos objects
            order = CmOrders.objects.prefetch_related('order_lines__product_variant').get(pk=order_id)
            cm_pos = CmPos.objects.get(id=cm_pos_id)

            # Get order data
            order_data = self.get_order_data(order, orderlines)

            # Generate HTML for the receipt
            html_receipt = self.generate_receipt_html(order_data)

            # Convert HTML to image
            img_data = self.convert_html_to_image(html_receipt)

            # Prepare data for the print service
            print_data = {
                'image_content': img_data.decode('latin1'),  # Convert bytes to string
                'printer_ip': cm_pos.printer_ip,  # Use the printer IP from CmPos
                'cashdraw': False
            }

            # Send the print job to the print service
            response = requests.post("http://192.168.1.128:5000/print", json=print_data)


            if response.status_code == 202:
                return Response({"message": "Print job sent successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Failed to send print job"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except CmOrders.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except CmPos.DoesNotExist:
            return Response({"error": "CmPos not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Print failed: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get_order_data(self, order, orderlines=None):
        site_settings = SiteSettings.objects.first()

        # If orderlines is None, get all order lines for the order
        if orderlines is None:
            orderlines = order.order_lines.values_list('id', flat=True)

        # Filter the order lines based on the provided or calculated IDs
        orderlines = order.order_lines.filter(id__in=orderlines)

        # Calculate the total amount as the sum of the prices of the filtered order lines
        total_amount = sum(line.price for line in orderlines)

        res = {
            'site_name': site_settings.name if site_settings else 'Default Site',
            'date': order.create_at.strftime('%d/%m/%Y %H:%M:%S'),
            'cashier': order.created_by.name,
            'order_ref': order.ref,
            'table': order.cm_table.name if order.cm_table else '',
            'items': [
                {
                    'name': line.product_variant.name,
                    'qty': line.qty,
                    'price': line.price,
                    'discount': line.discount_amount
                } for line in order.order_lines.filter(id__in=orderlines)
            ],
            'total_amount': total_amount,
            'discount_amount': order.discount_amount
        }
        print(res)
        return res

    def generate_receipt_html(self, order_data):
        html_template = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Receipt</title>
                <style>
                    body {
                        font-family: 'Courier New', Courier, monospace;
                        width: 576px;  /* Set width to match typical POS printer */
                        margin: 0 auto;
                        padding: 10px;
                        background-color: #fff;
                        color: #000;
                        font-size: 24px;  /* Increased font size for better readability */
                    }
                    .text {
                        font-size: 24px;
                        text-align: start;
                    }
                    .header, .footer, .items {
                        text-align: center;
                    }
                    .items {
                        margin-top: 20px;
                    }
                     thead {
                        border-top: 4px solid #000;
                        border-bottom: 4px solid #000;
                    }
                    .items table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    .items th, .items td {
                        border-bottom: 1px dashed #000;
                        padding: 5px;
                    }
                    .total, .paid {
                        width: 100%;
                        text-align: right;
                        font-size: 30px;
                        padding-right: 10px;
                    }
                    img {
                        max-width: 100%;
                    }
                    .flex {
                        display: flex;
                    }
                    .justify-between {
                        justify-content: space-between;
                    }
                    .separator {
                        width: 100%;
                        height: 4px;
                        background-color: black;
                    }
                    .line-through {
                        text-decoration: line-through;
                    }
                    .hidden {
                        display:none;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <img src="https://caissemanager.com/wp-content/uploads/2024/02/logo-web-1.png" width="200" />
                    <div class="flex justify-between">
                        <p>{{date}}</p>
                        <p>{{cashier}}</p>
                    </div>
                    <p>COMMANDE: *** {{order_ref}} ***</p>
                </div>

                <div class="items">
                    <table>
                        <thead>
                            <tr>
                                <th class="text">Article</th>
                                <th class="text">Qte</th>
                                <th class="text">Montant</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for item in items %}
                            <tr class="{{ 'line-through' if item.qty == 0 else '' }}">
                                <td class="text">{{item.name}}</td>
                                <td class="text">{{item.qty}}</td>
                                <td class="text">{{item.price}}</td>
                            </tr> 
                            
                            {% endfor %}
                        </tbody>
                    </table>
                    <div class="separator"></div>
                </div>

                <div class="total">
                    <p>MONTANT TOTAL: {{total_amount}} DH  -</p>
                    <p class="{{ 'hidden' if discount_amount == 0.0}}">
                        MONTANT Remise: {{discount_amount}} DH  -
                    </p>
                </div>
                <div class="footer">
                    <p>Merci pour votre visite</p>
                    <p>{{date}}</p>
                </div>
            </body>
            </html>
        """
        template = Template(html_template)
        return template.render(order_data)

    def convert_html_to_image(self, html_content):
        options = {
            'format': 'png',
            'width': '576',  # Set width to match typical POS printer
            'disable-smart-width': '',
            'quality': '100',
            'disable-plugins': '',
            'disable-javascript': '',
        }
        img = imgkit.from_string(html_content, False, options=options)
        return img

    def _create_order(self, data):
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return serializer.data

    @action(detail=False, methods=['get'])
    def by_table(self, request):
        table = request.query_params.get('table', None)
        if table is not None:
            orders = CmOrders.objects.filter(cm_table=table, status="New")
            if orders.exists():
                serializer = self.get_serializer(orders, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # Return 204 No Content if no orders are found
                return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "table query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_shift(self, request):
        shift_id = request.query_params.get('shift_id', None)
        if shift_id is not None:
            orders = CmOrders.objects.filter(cm_shift=shift_id)
            if orders.exists():
                serializer = self.get_serializer(orders, many=True)
                return Response(serializer.data)
            else:
                return Response({"message": "No orders found for this shift"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "shift_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'])
    def by_waiter_and_shift(self, request):
        waiter_id = request.query_params.get('waiter_id', None)
        shift_id = request.query_params.get('shift_id', None)

        if waiter_id is not None and shift_id is not None:
            orders = CmOrders.objects.filter(cm_waiter=waiter_id, cm_shift=shift_id)
            if orders.exists():
                serializer = self.get_serializer(orders, many=True)
                return Response(serializer.data)
            else:
                return Response({"message": "No orders found for this waiter and shift combination"}, status=status.HTTP_404_NOT_FOUND)
        else:
            missing_params = []
            if waiter_id is None:
                missing_params.append("waiter_id")
            if shift_id is None:
                missing_params.append("shift_id")
            return Response({"error": f"{', '.join(missing_params)} query parameter{' is' if len(missing_params) == 1 else 's are'} required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_day(self, request):
        current_day = CmDays.objects.filter(status="Open").first()
        if current_day:
            shifts = CmShifts.objects.filter(cm_day=current_day)
            orders = CmOrders.objects.filter(cm_shift__in=shifts)
            if orders.exists():
                serializer = self.get_serializer(orders, many=True)
                return Response(serializer.data)
                
            else:
                return Response({"message": "No orders found for the current day"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "No shifts found for the current day"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='order/(?P<order_id>[^/.]+)')
    def by_order_id(self, request, order_id=None):
        try:
            order = CmOrders.objects.get(id=order_id)
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        except CmOrders.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

@permission_classes([IsAuthenticated])
class CmOrderLineViewSet(viewsets.ModelViewSet):
    queryset = CmOrderLine.objects.all()
    serializer_class = CmOrderLineSerializer

    @action(detail=False, methods=['get'])
    def suite_ordred(self, request):
        """
        Update the suite_ordred field of an order line and related KDS order lines if suite_commande is True.
        Notify the kitchen display via a socket request.
        """
        orderline_id = request.query_params.get('orderline_id', None)
        if orderline_id is None:
            return Response({"error": "orderline_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            orderline = CmOrderLine.objects.get(id=orderline_id)

            # Check if suite_commande is True before updating suite_ordred
            if orderline.suite_commande:
                # Update suite_ordred to True
                orderline.suite_ordred = True
                orderline.save()

                # Update related KDS order lines
                related_kds_orderlines = CmKdsOrderline.objects.filter(cm_pos_orderline=orderline)

                for kds_orderline in related_kds_orderlines:
                    kds_orderline.suiteOrdred = True
                    kds_orderline.save()

                # Prepare the data to send to the socket server
                kds_order_data = {
                    "orderline_id": orderline.id,
                    "suite_ordred": orderline.suite_ordred,
                    "data": [
                        {
                            "preparation_display_id": kds_orderline.cm_kds_order.cm_preparation_display.id,
                            "kds_order_id": kds_orderline.cm_kds_order.id,
                            "kds_orderline_id": kds_orderline.id,
                        }
                        for kds_orderline in related_kds_orderlines
                    ],
                }

                # Send the data to the socket server
                try:
                    response = requests.post(socket_server_url +"/notify-suite-ordred", json=kds_order_data)
                    response.raise_for_status()  # Raise an error for bad status codes
                except requests.exceptions.RequestException as e:
                    return Response({"error": f"Failed to notify the kitchen display: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({"message": "Order line and related KDS order lines updated successfully. Kitchen display notified."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "suite_commande is False. Cannot update suite_ordred."}, status=status.HTTP_400_BAD_REQUEST)

        except CmOrderLine.DoesNotExist:
            return Response({"error": "Order line not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Failed to update suite_ordred: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@permission_classes([IsAuthenticated])
class CmOrderTypeViewSet(viewsets.ModelViewSet):
    queryset = CmOrderType.objects.filter(parent__isnull=True)
    serializer_class = CmOrderTypeSerializer
    permission_classes = [IsAuthenticated]

@permission_classes([IsAuthenticated])
class DiscountsViewSet(viewsets.ModelViewSet):
    queryset = Discounts.objects.all()
    serializer_class = DiscountsSerializer

    @action(detail=False, methods=['get'])
    def by_shift(self, request):
        shift_id = request.query_params.get('shift_id', None)
        if shift_id:
            discounts = Discounts.objects.filter(order__cm_shift_id=shift_id)
            serializer = self.get_serializer(discounts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "shift_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_day(self, request):
        day_id = request.query_params.get('day_id', None)
        if day_id:
            discounts = Discounts.objects.filter(order__cm_shift__cm_day_id=day_id)
            serializer = self.get_serializer(discounts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "day_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def apply_discount(self, request):
        data = request.data
        discount_type_id = data.get('discount_type')
        order_id = data.get('order')
        orderline_id = data.get('orderline')

        try:
            discount_type = DiscountType.objects.get(id=discount_type_id)
            discount_value = discount_type.value
            discount_amount = 0.0

            with transaction.atomic():
                if order_id:
                    # Apply discount to order
                    order = CmOrders.objects.get(id=order_id)
                    if discount_type.type == 'percentage':
                        discount_amount = (discount_value / 100.0) * order.total_amount
                    elif discount_type.type == 'amount':
                        discount_amount = discount_value

                    order.discount_amount += discount_amount
                    order.total_amount -= discount_amount
                    order.save()

                    # Create discount record
                    Discounts.objects.create(
                        name=discount_type.name,
                        discount_type=discount_type,
                        order=order,
                        orderline=None
                    )

                    return Response({"message": "Discount applied to order successfully"}, status=status.HTTP_200_OK)

                elif orderline_id:
                    # Apply discount to order line
                    orderline = CmOrderLine.objects.get(id=orderline_id)
                    if discount_type.type == 'percentage':
                        discount_amount = (discount_value / 100.0) * orderline.price
                    elif discount_type.type == 'amount':
                        discount_amount = discount_value

                    orderline.discount_amount += discount_amount
                    orderline.price -= discount_amount
                    orderline.save()

                    # Recalculate total order price
                    order = orderline.order
                    order_total = sum(line.price for line in order.order_lines.all())
                    order.total_amount = order_total
                    order.save()

                    # Create discount record
                    Discounts.objects.create(
                        name=discount_type.name,
                        discount_type=discount_type,
                        order=None,
                        orderline=orderline
                    )

                    return Response({"message": "Discount applied to order line successfully"}, status=status.HTTP_200_OK)

                else:
                    return Response({"error": "Either order or orderline must be specified"}, status=status.HTTP_400_BAD_REQUEST)

        except DiscountType.DoesNotExist:
            return Response({"error": "Discount type not found"}, status=status.HTTP_404_NOT_FOUND)

        except (CmOrders.DoesNotExist, CmOrderLine.DoesNotExist):
            return Response({"error": "Order or OrderLine not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Failed to apply discount: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@permission_classes([IsAuthenticated])
class OrderCancelViewSet(viewsets.ModelViewSet):
    queryset = OrderCancel.objects.all()
    serializer_class = OrderCancelSerializer

    @action(detail=False, methods=['get'])
    def by_shift(self, request):
        shift_id = request.query_params.get('shift_id', None)
        if shift_id:
            order_cancels = OrderCancel.objects.filter(order__cm_shift_id=shift_id)
            serializer = self.get_serializer(order_cancels, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "shift_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_day(self, request):
        day_id = request.query_params.get('day_id', None)
        if day_id:
            order_cancels = OrderCancel.objects.filter(order__cm_shift__cm_day_id=day_id)
            serializer = self.get_serializer(order_cancels, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "day_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def cancel_order_or_line(self, request):
        data = request.data
        order_id = data.get('order')
        orderline_id = data.get('orderline')
        quantity = data.get('quantity', 0)
        created_by_id = data.get('created_by')
        reason = data.get('reason', '')

        try:
            with transaction.atomic():
                if order_id:
                    # Cancel entire order
                    order = CmOrders.objects.get(id=order_id)
                    order.status = "Cancelled"
                    order.save()

                    # Remove all discounts related to the order
                    Discounts.objects.filter(order=order).delete()

                    # Create order cancellation record
                    OrderCancel.objects.create(
                        order=order,
                        orderline=None,
                        created_by_id=created_by_id,
                        reason=reason
                    )

                    # Search for all KDS orders related to the order's POS order
                    kds_orders = CmKdsOrder.objects.filter(cm_pos_order=order)

                    # Update the status of all related KDS orders to "Cancelled"
                    kds_orders.update(cancelled=True)

                    # Prepare the data for socket notification
                    kds_order_data = {
                        "order_id": order_id,
                        "type": "Order",
                        "data": [
                            {
                                "preparation_display_id": kds_order.cm_preparation_display.id,
                                "kds_order_id": kds_order.id
                            }
                            for kds_order in kds_orders
                        ],
                    }

                    # Notify the front-end via the socket server
                    self.notify_cancel_via_socket(kds_order_data)

                    return Response({"message": "Order cancelled successfully"}, status=status.HTTP_200_OK)

                elif orderline_id:
                    # Cancel part of an order line
                    orderline = CmOrderLine.objects.get(id=orderline_id)
                    original_qty = orderline.qty
                    cancelled_qty = min(quantity, original_qty)

                    if cancelled_qty > 0:
                        orderline.cancelled_qty += cancelled_qty
                        orderline.qty -= cancelled_qty

                        # Recalculate the price and discount
                        self.recalculate_orderline_price_and_discount(orderline)

                        orderline.save()

                        # Create order line cancellation record
                        OrderCancel.objects.create(
                            order=orderline.order,
                            orderline=orderline,
                            quantity=cancelled_qty,
                            created_by_id=created_by_id,
                            reason=reason
                        )

                        # Recalculate the total order amount
                        self.recalculate_order_total(orderline.order)

                        # Search for all KDS order lines related to the order line's POS order line
                        related_kds_orderlines = CmKdsOrderline.objects.filter(cm_pos_orderline=orderline)

                        # Update the quantity_cancelled attribute for all related KDS order lines
                        for kds_orderline in related_kds_orderlines:
                            kds_orderline.quantity_cancelled += cancelled_qty
                            kds_orderline.save()

                        # Prepare the data for socket notification
                        kds_order_data = {
                            "orderline_id": orderline.id,
                            "type": "Orderline",
                            "data": [
                                {
                                    "preparation_display_id": kds_orderline.cm_kds_order.cm_preparation_display.id,
                                    "kds_order_id": kds_orderline.cm_kds_order.id,
                                    "kds_orderline_id": kds_orderline.id,
                                    "cancelled_qty": cancelled_qty  # Include the cancelled quantity
                                }
                                for kds_orderline in related_kds_orderlines
                            ],
                        }

                        # Notify the front-end via the socket server
                        self.notify_cancel_via_socket(kds_order_data)

                        return Response({"message": "Order line cancelled successfully"}, status=status.HTTP_200_OK)

                return Response({"error": "Either order or orderline must be specified"}, status=status.HTTP_400_BAD_REQUEST)

        except (CmOrders.DoesNotExist, CmOrderLine.DoesNotExist):
            return Response({"error": "Order or OrderLine not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Failed to cancel order or line: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def notify_cancel_via_socket(self, cancel_data):
        url = socket_server_url + '/notify-cancel-order-or-line'
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(url, data=json.dumps(cancel_data), headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to notify socket server: {str(e)}")

    def recalculate_orderline_price_and_discount(self, orderline):
        # Check if there are any discounts applied to the order line
        discount = Discounts.objects.filter(orderline=orderline).first()
        
        if discount:
            if orderline.qty == 0:
                # If the quantity is zero, remove any discounts related to the order line
                discount.delete()
            else:
                # Recalculate the discount amount based on the new quantity
                if discount.discount_type.type == 'percentage':
                    discount_amount = (orderline.qty * orderline.product_variant.price_ttc) * (discount.discount_type.value / 100)
                elif discount.discount_type.type == 'amount':
                    discount_amount = discount.discount_type.value
                else:
                    discount_amount = 0

                # Ensure discount amount does not exceed the price
                discount_amount = min(discount_amount, orderline.qty * orderline.product_variant.price_ttc)
                
                # Update the discount amount on the order line
                orderline.discount_amount = discount_amount
                discount.save()

        # Update the price of the order line based on the new quantity and discount
        orderline.price = (orderline.qty * orderline.product_variant.price_ttc) - orderline.discount_amount

    def recalculate_order_total(self, order):
        # Calculate the new total amount for the order
        order.total_amount = order.order_lines.aggregate(total=Sum('price'))['total'] or 0.0
        order.save()