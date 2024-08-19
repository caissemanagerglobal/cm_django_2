from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from server.settings import socket_server_url
from .models import CmPreparationDisplayStage, CmPreparationDisplay, CmKdsOrder, CmKdsOrderline
from products.models import KitchenPoste,Category
from products.serializers import CategoryGetSerializer, ProductVariantSerializer
from .serializers import CmPreparationDisplayStageSerializer, CmPreparationDisplaySerializer, CmKdsOrderSerializer, CmKdsOrderlineSerializer
import requests
import json

@permission_classes([IsAuthenticated])
class CmPreparationDisplayStageViewSet(viewsets.ModelViewSet):
    queryset = CmPreparationDisplayStage.objects.all()
    serializer_class = CmPreparationDisplayStageSerializer


@permission_classes([IsAuthenticated])
class CmPreparationDisplayViewSet(viewsets.ModelViewSet):
    queryset = CmPreparationDisplay.objects.all()
    serializer_class = CmPreparationDisplaySerializer


    @action(detail=False, methods=['get'])
    def get_categories_and_products(self, request):
        preparation_display_id = request.query_params.get('preparation_display_id', None)
        if not preparation_display_id:
            return Response({"error": "preparation_display_id is required"}, status=400)

        try:
            # Find the kitchen poste that has the provided preparation_display_id
            kitchen_poste = KitchenPoste.objects.get(screen_poste_id=preparation_display_id)

            # Fetch product variants associated with the kitchen poste
            products = kitchen_poste.product_variants.filter(is_active=True)

            # Fetch categories and order types
            categories = Category.objects.filter(is_displayed=True)

            # Serialize the data
            categories_data = CategoryGetSerializer(categories, many=True).data
            products_data = ProductVariantSerializer(products, many=True).data

            # Prepare the response data
            response_data = {
                'categories': categories_data,
                'products': products_data
            }

            return Response(response_data, status=200)

        except KitchenPoste.DoesNotExist:
            return Response({"error": "KitchenPoste with the given preparation_display_id does not exist"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


    @action(detail=False, methods=['get'])
    def display_orders_by_stage(self, request):
        try:
            # Get the preparation_display_id and stage_id from the request parameters
            preparation_display_id = request.query_params.get('preparation_display_id', None)
            stage_id = request.query_params.get('stage_id', None)

            if not preparation_display_id:
                return Response({"error": "preparation_display_id is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the preparation display object
            preparation_display = CmPreparationDisplay.objects.get(id=preparation_display_id)

            # Filter orders based on the provided stage_id, if given
            if stage_id:
                kds_orders = CmKdsOrder.objects.filter(
                    cm_preparation_display=preparation_display,
                    cm_preparation_display_stage_id=stage_id,
                    is_displayed=True
                )
            else:
                kds_orders = CmKdsOrder.objects.filter(
                    cm_preparation_display=preparation_display,
                    is_displayed=True
                )

            # Construct the custom response format for each order
            orders_data = []
            for order in kds_orders:
                order_data = {
                    "id": order.id,
                    "table": order.cm_pos_order.cm_table.name if order.cm_pos_order.cm_table else None,
                    "waiter": order.cm_pos_order.cm_waiter.name if order.cm_pos_order.cm_waiter else None,
                    "orderType": order.cm_pos_order.cm_order_type.id,
                    "ref": order.cm_pos_order.ref,
                    "customer_count": order.cm_pos_order.customer_count,
                    "create_date": order.create_at,
                    "pos_order_id":order.cm_pos_order.id,
                    "status": order.status,
                    "orderlines": []
                }

                # Loop through each order line
                for orderline in order.kds_order_orderline.all():
                    orderline_data = {
                        "qty": orderline.cm_pos_orderline.qty,
                        "pos_orderline_id": orderline.cm_pos_orderline.id,
                        "product": orderline.cm_pos_orderline.product_variant.name,
                        "suite_commande": orderline.suiteCommande,
                        "suiteOrdred": orderline.suiteOrdred,
                        "notes": orderline.cm_pos_orderline.notes,
                        "qty_cancelled": orderline.cm_pos_orderline.cancelled_qty,
                        "clientIndex": orderline.cm_pos_orderline.customer_index,
                        "orderType": orderline.cm_pos_orderline.cm_order_type.id,
                        "is_done": orderline.is_done,
                        "combo_prod_ids": list(orderline.cm_pos_orderline.combo_prods.values_list('name', flat=True))
                    }
                    order_data["orderlines"].append(orderline_data)

                orders_data.append(order_data)

            return Response({
                'preparation_display': CmPreparationDisplaySerializer(preparation_display).data,
                'stage_id': stage_id,
                'orders': orders_data
            })

        except CmPreparationDisplay.DoesNotExist:
            return Response({"error": "Preparation display not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def display_orders(self, request, pk=None):
        try:
            preparation_display_id = request.query_params.get('preparation_display_id', None)
            if not preparation_display_id:
                return Response({"error": "preparation_display_id is required."}, status=status.HTTP_400_BAD_REQUEST)

            preparation_display = CmPreparationDisplay.objects.get(id=preparation_display_id)
            stages = preparation_display.stage_ids

            stages_data = CmPreparationDisplayStageSerializer(stages,many=True).data
            
            kds_orders = CmKdsOrder.objects.filter(
                cm_preparation_display=preparation_display,
                is_displayed=True
            )
            # kds_order_serializer = CmKdsOrderSerializer(kds_orders, many=True)
            orders_data = []
            for order in kds_orders:
                order_data = {
                    "id": order.id,
                    "cancelled": order.cancelled,
                    "pos_order_id": order.cm_pos_order.id,
                    "table": order.cm_pos_order.cm_table.name if order.cm_pos_order.cm_table else None,
                    "waiter": order.cm_pos_order.cm_waiter.name if order.cm_pos_order.cm_waiter else None,
                    "orderType": order.cm_pos_order.cm_order_type.id,
                    "ref": order.cm_pos_order.ref,
                    "customer_count": order.cm_pos_order.customer_count,
                    "create_date": order.create_at,
                    "stage_id": order.cm_preparation_display_stage.id,
                    "orderlines": []
                }

                # Loop through each order line
                for orderline in order.kds_order_orderline.all():
                    orderline_data = {
                        "id":orderline.id,
                        "pos_orderline_id": orderline.cm_pos_orderline.id,
                        "qty": orderline.cm_pos_orderline.qty,
                        "product": orderline.cm_pos_orderline.product_variant.name,
                        "suite_commande": orderline.suiteCommande,
                        "suiteOrdred": orderline.suiteOrdred,
                        "notes": orderline.cm_pos_orderline.notes,
                        "qty_cancelled": orderline.cm_pos_orderline.cancelled_qty,
                        "clientIndex": orderline.cm_pos_orderline.customer_index,
                        "orderType": orderline.cm_pos_orderline.cm_order_type.id,
                        "is_done": orderline.is_done,
                        "combo_prod_ids": list(orderline.cm_pos_orderline.combo_prods.values_list('name', flat=True))
                    }
                    order_data["orderlines"].append(orderline_data)

                orders_data.append(order_data)

            return Response({
                'orders': orders_data,
                'stages':stages_data
            })
        except CmPreparationDisplay.DoesNotExist:
            return Response({"error": "Preparation display not found."}, status=status.HTTP_404_NOT_FOUND)



@permission_classes([IsAuthenticated])
class CmKdsOrderViewSet(viewsets.ModelViewSet):
    queryset = CmKdsOrder.objects.all()
    serializer_class = CmKdsOrderSerializer


    @action(detail=False, methods=['get'])
    def change_stage(self, request):
        try:
            # Get the kds_order_id from the request parameters
            kds_order_id = request.query_params.get('kds_order_id', None)
            if not kds_order_id:
                return Response({"error": "kds_order_id is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the KDS order
            kds_order = CmKdsOrder.objects.get(id=kds_order_id)

            # Get the current stage and sequence
            current_stage = kds_order.cm_preparation_display_stage
            current_sequence = current_stage.sequence

            # Find the next stage based on sequence
            next_stage = CmPreparationDisplayStage.objects.filter(
                sequence=current_sequence + 1
            ).first()

            if not next_stage:
                return Response({"error": "No next stage found. The order may already be at the final stage."}, status=status.HTTP_400_BAD_REQUEST)

            # Update the KDS order's stage
            kds_order.cm_preparation_display_stage = next_stage
            kds_order.save()

            # Find all KDS orders in the same group that are in the current stage
            related_kds_orders = CmKdsOrder.objects.filter(
                group_id=kds_order.group_id,
                cm_preparation_display__is_pilotage=False,
                cm_preparation_display_stage=current_stage
            ).exclude(id=kds_order.id)

            # If any related KDS order is still in the current stage, do not move the pilotage order yet
            if related_kds_orders.exists():
                return Response({
                    "message": "Order stage updated successfully, but pilotage order has not been updated yet.",
                    "order_id": kds_order.id,
                    "new_stage": CmPreparationDisplayStageSerializer(next_stage).data
                }, status=status.HTTP_200_OK)

            # Find the pilotage KDS order in the same group
            pilotage_order = CmKdsOrder.objects.filter(
                group_id=kds_order.group_id,
                cm_preparation_display__is_pilotage=True
            ).first()

            if pilotage_order:
                pilotage_order.cm_preparation_display_stage = next_stage
                pilotage_order.save()
                # Notify the front-end via the new specific socket server endpoint
                url = socket_server_url + '/notify-pilotage-order-state'
                payload = {
                    "order_id": pilotage_order.id,
                    "new_stage": CmPreparationDisplayStageSerializer(next_stage).data
                }
                headers = {'Content-Type': 'application/json'}

                try:
                    response = requests.post(url, data=json.dumps(payload), headers=headers)
                    response.raise_for_status() 
                except requests.exceptions.RequestException as e:
                    return Response({"error": f"Failed to notify socket server: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                

            return Response({
                "message": "Order stage updated successfully, and pilotage order also moved to the next stage.",
                "order_id": kds_order.id,
                "new_stage": CmPreparationDisplayStageSerializer(next_stage).data
            }, status=status.HTTP_200_OK)

        except CmKdsOrder.DoesNotExist:
            return Response({"error": "KDS order not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        try:
            # Get the preparation display ID from the request parameters
            preparation_display_id = request.query_params.get('preparation_display_id', None)
            if not preparation_display_id:
                return Response({"error": "preparation_display_id is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Get the stage with sequence 3
            stage = CmPreparationDisplayStage.objects.filter(sequence=3).first()
            if not stage:
                return Response({"error": "Stage with sequence 3 not found."}, status=status.HTTP_404_NOT_FOUND)

            # Update the is_displayed field to False for all orders with the given preparation_display_id and stage
            affected_rows = CmKdsOrder.objects.filter(
                cm_preparation_display_id=preparation_display_id,
                cm_preparation_display_stage=stage
            ).update(is_displayed=False)

            return Response({
                "message": f"{affected_rows} orders have been cleared successfully.",
                "affected_rows": affected_rows
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@permission_classes([IsAuthenticated])
class CmKdsOrderlineViewSet(viewsets.ModelViewSet):
    queryset = CmKdsOrderline.objects.all()
    serializer_class = CmKdsOrderlineSerializer


    @action(detail=True, methods=['get'])
    def toggle_is_done(self, request, pk=None):
        try:
            orderline = request.query_params.get('orderline', None)
            is_done = request.query_params.get('is_done', None)
            if is_done == 'true':
                is_done = True
            elif is_done == 'false':
                is_done = False
            print(is_done)
            if not orderline and not is_done:
                return Response({"error": "orderline and is_done is required."}, status=status.HTTP_400_BAD_REQUEST)

            orderline = CmKdsOrderline.objects.get(id=orderline)

            orderline.is_done = is_done
            orderline.save()

            return Response({
                "message": "Order line 'is_done' value toggled successfully.",
                "orderline_id": orderline.id,
                "is_done": orderline.is_done
            }, status=status.HTTP_200_OK)

        except CmKdsOrderline.DoesNotExist:
            return Response({"error": "Order line not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)