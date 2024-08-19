from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from orders.models import CmOrderLine, CmOrders
from pos.models import CmShifts, CmPos
from core.models import SiteSettings, DiscountType
from .models import CmClosingBalances, CmClientDebts, CmPayments, CmDrops, CmPaymentMethods, CmPaymentMethodsAttributes
from .serializers import CmClosingBalancesSerializer, CmClientDebtsSerializer, CmPaymentsSerializer, CmDropsSerializer, CmPaymentMethodsSerializer, CmPaymentMethodsAttributesSerializer
from .tasks import process_payment_sync  # Import the synchronous payment processing function
import threading
from django.db.models import Sum

import requests
from escpos.printer import Network
from jinja2 import Template
import imgkit
import weasyprint
import logging

logger = logging.getLogger(__name__)

@permission_classes([IsAuthenticated])
class CmClosingBalancesViewSet(viewsets.ModelViewSet): 
    queryset = CmClosingBalances.objects.all()
    serializer_class = CmClosingBalancesSerializer

    @action(detail=False, methods=['get'], url_path='by-shift/(?P<shift_id>[^/.]+)')
    def get_by_shift(self, request, shift_id=None):
        closing_balances = CmClosingBalances.objects.filter(cm_shift_id=shift_id)
        serializer = self.get_serializer(closing_balances, many=True)
        return Response(serializer.data)

@permission_classes([IsAuthenticated])
class CmClientDebtsViewSet(viewsets.ModelViewSet):
    queryset = CmClientDebts.objects.all()
    serializer_class = CmClientDebtsSerializer

@permission_classes([IsAuthenticated])
class CmPaymentsViewSet(viewsets.ModelViewSet):
    queryset = CmPayments.objects.all()
    serializer_class = CmPaymentsSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        orderline_ids = data.get('orderlines', [])
        payment_data = data.get('payment', {})
        amount_given = payment_data.get('amount_given', 0)
        amount_return = payment_data.get('amount_return', 0)


        # Validate that both orderlines and payment data are provided
        if not orderline_ids or not payment_data:
            return Response({"error": "Both orderlines and payment data must be provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create the payment object
            payment = CmPayments.objects.create(
                cm_order_id=payment_data['cm_order'],
                amount=payment_data['amount'],
                cm_shift_id=payment_data['cm_shift'],
                cm_payment_method_id=payment_data['cm_payment_method']
            )
            payment_method = CmPaymentMethods.objects.get(id=payment_data['cm_payment_method'])
            shift = CmShifts.objects.get(id=payment_data['cm_shift'])
            print = self.print_ticket(payment_data['cm_order'],shift.cm_pos.id,amount_given, amount_return, payment_method.name, orderline_ids)

            # Update order lines to set them as paid
            CmOrderLine.objects.filter(id__in=orderline_ids).update(is_paid=True)

            # Check if the order is fully paid
            cm_order = CmOrders.objects.get(id=payment_data['cm_order'])
            total_paid = CmPayments.objects.filter(cm_order=cm_order).aggregate(total=Sum('amount'))['total'] or 0
            total_order_amount = cm_order.total_amount

            if total_paid >= total_order_amount:
                cm_order.status = 'Paid'
                cm_order.save()

            return Response({"message": "Payment processed successfully", "payment_id": payment.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        

        
    def print_ticket(self, order_id, cm_pos_id, amount_given, amount_return, payment_method, orderline_ids):
        try:
            # Extract order_id and cm_pos from the request data
            order_id = order_id
            cm_pos_id = cm_pos_id

            if not order_id or not cm_pos_id:
                return Response({"error": "order_id and cm_pos are required."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the order and CmPos objects
            order = CmOrders.objects.prefetch_related('order_lines__product_variant').get(pk=order_id)
            cm_pos = CmPos.objects.get(id=cm_pos_id)

            # Get order data
            order_data = self.get_order_data(order, orderline_ids)

            # Generate HTML for the receipt
            html_receipt = self.generate_receipt_html(order_data,amount_given, amount_return, payment_method)

            # Convert HTML to image
            img_data = self.convert_html_to_image(html_receipt)

            # Prepare data for the print service
            print_data = {
                'image_content': img_data.decode('latin1'),  # Convert bytes to string
                'printer_ip': cm_pos.printer_ip,  # Use the printer IP from CmPos
                'cashdraw': True
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

    def get_order_data(self, order, orderline_ids=None):
        # Extract order data for rendering
        site_settings = SiteSettings.objects.first()

        if orderline_ids is None:
            orderline_ids = order.order_lines.values_list('id', flat=True)

        # Filter the order lines based on the provided or calculated IDs
        orderlines = order.order_lines.filter(id__in=orderline_ids)

        # Calculate the total amount as the sum of the prices of the filtered order lines
        total_amount = sum(line.price for line in orderlines)

        return {
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
                } for line in orderlines
            ], 
            'total_amount': total_amount,
        }



    def generate_receipt_html(self, order_data,amount_given, amount_return, payment_method):
        order_data["amount_given"] = amount_given
        order_data["amount_return"] = amount_return
        order_data["payment_method"] = payment_method
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
                    .subtotal{
                        width: 100%;
                        text-align: right;
                        font-size: 20px;
                        padding-right: 10px;
                        border-bottom-style: dotted;
                    }
                    img {
                        max-width: 100%;
                    }
                    .w-50{
                        width: 100%;
                    }
                    .flex {
                        display: flex;
                    }
                    .footer{
                  		font-size: 15px;
    					font-weight: 100;
                  	}
                    .justify-between {
                        justify-content: space-between;
                    }
                    .separator {
                        width: 100%;
                        height: 4px;
                        background-color: black;
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
                            <tr>
                                <td class="text">{{item.name}}</td>
                                <td class="text">{{item.qty}}</td>
                                <td class="text">{{item.price}}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    <div class="separator"></div>
                </div>
                <div class="">
                    <div class="total">
                        <p>MONTANT TOTAL: {{total_amount}} DH  -</p>
                    </div>
                    <div class="subtotal">
                      
                      	<p>DONNEE: {{amount_given}} DH  -</p>
						<p>A RENDRE: {{amount_return}} DH  -</p>
                        <div class="flex w-50 " style="border-top-style: dotted;">
                            <p>
                                PAIMENT:
                            </p>
                            <p> {{payment_method}}</p>
                        </div>
                        
                        
                    </div>
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






    # @action(detail=False, methods=['get'], url_path='order/(?P<order>[^/.]+)')
    @action(detail=False, methods=['get'])
    def by_order(self, request, order=None):
        # payments = CmPayments.objects.filter(cm_order=order)
        # serializer = self.get_serializer(payments, many=True)
        # return Response(serializer.data)
    
        order = request.query_params.get('order', None)
        if order is not None:
            payments = CmPayments.objects.filter(cm_order=order)
            serializer = self.get_serializer(payments, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "order query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    # @action(detail=False, methods=['get'], url_path='payment-method/(?P<payment_method>[^/.]+)')
    @action(detail=False, methods=['get'])
    def by_payment_method(self, request):
        payment_method = request.query_params.get('payment_method', None)
        if payment_method is not None:
            payments = CmPayments.objects.filter(cm_payment_method=payment_method)
            serializer = self.get_serializer(payments, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "payment_method query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_shift(self, request):
        shift_id = request.query_params.get('shift_id', None)
        if shift_id is not None:
            payments = CmPayments.objects.filter(cm_order__cm_shift=shift_id)
            serializer = self.get_serializer(payments, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "shift_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_day(self, request):
        day_id = request.query_params.get('day_id', None)
        if day_id is not None:
            payments = CmPayments.objects.filter(cm_order__cm_shift__cm_day_id=day_id)
            serializer = self.get_serializer(payments, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "day_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

@permission_classes([IsAuthenticated])
class CmDropsViewSet(viewsets.ModelViewSet):
    queryset = CmDrops.objects.all()
    serializer_class = CmDropsSerializer

    @action(detail=False, methods=['get'])
    def by_shift(self, request):
        shift_id = request.query_params.get('shift_id', None)
        if shift_id is not None:
            drops = CmDrops.objects.filter(cm_shift_id=shift_id)
            serializer = self.get_serializer(drops, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "shift_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_day(self, request):
        day_id = request.query_params.get('day_id', None)
        if day_id is not None:
            drops = CmDrops.objects.filter(cm_shift__cm_day_id=day_id)
            serializer = self.get_serializer(drops, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "day_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

@permission_classes([IsAuthenticated])
class CmPaymentMethodsViewSet(viewsets.ModelViewSet):
    queryset = CmPaymentMethods.objects.all()
    serializer_class = CmPaymentMethodsSerializer



@permission_classes([IsAuthenticated])
class CmPaymentMethodsAttributesViewSet(viewsets.ModelViewSet):
    queryset = CmPaymentMethodsAttributes.objects.all()
    serializer_class = CmPaymentMethodsAttributesSerializer

    @action(detail=False, methods=['get'], url_path='by-payment-method/(?P<payment_method_id>[^/.]+)')
    def get_by_payment_method(self, request, payment_method_id=None):
        attributes = CmPaymentMethodsAttributes.objects.filter(payment_method_id=payment_method_id)
        serializer = self.get_serializer(attributes, many=True)
        return Response(serializer.data)
