# views.py

from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework_api_key.permissions import HasAPIKey
import math
from rest_framework.permissions import IsAuthenticated
from .models import CmDays, CmPos, CmTable, CmShifts, CmFloor
from .serializers import CmDaysSerializer, CmPosSerializer, CmTableSerializer, CmShiftsSerializer, CmFloorSerializer
from core.models import ConfigSettings, DefinedNotes, DiscountType
from core.serializers import ConfigSettingsSerializer, DefinedNotesSerializer, DiscountTypeSerializer
from products.models import Category
from products.serializers  import CategorySerializer
from orders.models import CmOrderType, CmOrders
from kds.models import CmKdsOrder
from django.db.models import Sum  
from orders.serializers import CmOrderTypeSerializer, CmOrderTypeKdsSerializer
from users.models import CmEmployees,CmClients
from users.serializers import CmClientsSerializer, CmEmployeesSerializer
from payments.models import CmPaymentMethods, CmPayments, CmClosingBalances, CmDrops
from payments.serializers import CmPaymentMethodsSerializer
from users.models import CmEmployees
from django.utils import timezone
from django.db import transaction
from server.settings import admin_pass
from rest_framework.views import APIView
from datetime import date
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('django')


@permission_classes([IsAuthenticated])
class DashboardMetricsDayAPIView(APIView):
    def get(self, request):
        try:
            # Get the last closed CmDay
            last_closed_cmday = CmDays.objects.filter(status='Closed').order_by('-closing_time').first()
            
            if last_closed_cmday:
                # Calculate the revenue for the last closed CmDay using the model's property
                last_cmday_revenue_system = last_closed_cmday.revenueSystem
                
                # Count the number of orders for the last closed CmDay
                last_cmday_orders_count = last_closed_cmday.day_shifts.aggregate(
                    total_orders=Sum('cmshiftorders__order_count')
                )['total_orders'] or 0
                
                # Count the number of shifts for the last closed CmDay
                last_cmday_shifts_count = last_closed_cmday.day_shifts.count()
                
                metrics = [
                    {"name": "Revenue Last Closed Day (System)", "value": last_cmday_revenue_system},
                    {"name": "Total Orders Last Closed Day", "value": last_cmday_orders_count},
                    {"name": "Total Shifts Last Closed Day", "value": last_cmday_shifts_count}
                ]
                
                return Response(metrics, status=status.HTTP_200_OK)
            else:
                return Response({"error": "No closed CmDay found."}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@permission_classes([IsAuthenticated])
class DashboardMetricsAPIView(APIView):
    def get(self, request):
        try:
            today = datetime.today()
            first_day_of_month = today.replace(day=1)
            
            monthly_revenue = CmOrders.objects.filter(
                create_at__gte=first_day_of_month,
                create_at__lte=today
            ).aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0.0
            
            monthly_orders_count = CmOrders.objects.filter(
                create_at__gte=first_day_of_month,
                create_at__lte=today
            ).count()
            
            average_order_value = 0.0
            if monthly_orders_count > 0:
                average_order_value = monthly_revenue / monthly_orders_count

            today_orders_count = CmOrders.objects.filter(
                create_at__date=today.date()
            ).count()
            
            today_revenue = CmOrders.objects.filter(
                create_at__date=today.date()
            ).aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0.0
            
            metrics = [
                {"name": "Revenue Monthly", "value": monthly_revenue},
                {"name": "Total Orders Monthly", "value": monthly_orders_count},
                {"name": "Average Order Value Monthly", "value": average_order_value},
                {"name": "Total Orders Today", "value": today_orders_count},
                {"name": "Revenue Today", "value": today_revenue}
            ]
            
            return Response(metrics, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@permission_classes([IsAuthenticated])
class PasswordCheckViewSet(viewsets.ModelViewSet):

    @action(detail=False, methods=['post'])
    def check_password(self, request):
        try:
            password = request.data.get('password', None)

            if password is None:
                return Response({"error": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)

            if password != admin_pass:
                return Response({"error": "Invalid password."}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Password verified successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@permission_classes([IsAuthenticated])
class GeneralDataViewSet(APIView):


    def replace_invalid_floats(self,data):
        if isinstance(data, dict):
            return {k: self.replace_invalid_floats(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.replace_invalid_floats(item) for item in data]
        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return None  # or return "NaN" / "Infinity" / "-Infinity" as strings if you prefer
        return data

    def get(self, request):
        config = ConfigSettings.objects.all()
        floors = CmFloor.objects.all()
        categories = Category.objects.filter(parent__isnull=True, is_displayed=True)
        notes = DefinedNotes.objects.all()
        discounts = DiscountType.objects.all()
        order_types = CmOrderType.objects.filter(parent__isnull=True)
        clients = CmClients.objects.all()
        payment_methods = CmPaymentMethods.objects.all()

        waiters = CmEmployees.objects.filter(position="Serveur")
        delivery_guys = CmEmployees.objects.filter(position="Livreur")
        cashiers = CmEmployees.objects.filter(position="Caissier")

        floors_data = CmFloorSerializer(floors, many=True).data
        config_data = ConfigSettingsSerializer(config, many=True).data
        categories_data = CategorySerializer(categories, many=True).data
        notes_data = DefinedNotesSerializer(notes, many=True).data
        discounts_data = DiscountTypeSerializer(discounts, many=True).data
        order_types_data = CmOrderTypeSerializer(order_types, many=True).data
        clients_data = CmClientsSerializer(clients, many=True).data
        payment_methods_data = CmPaymentMethodsSerializer(payment_methods, many=True).data

        waiters_data = CmEmployeesSerializer(waiters, many=True).data
        delivery_guys_data = CmEmployeesSerializer(delivery_guys, many=True).data
        cashiers_data = CmEmployeesSerializer(cashiers, many=True).data

        response_data = {
            'floors': floors_data,
            'categories': categories_data,
            'config': config_data,
            'notes': notes_data,
            'discounts': discounts_data,
            'order-types': order_types_data,
            'clients': clients_data,
            'payment-methods': payment_methods_data,
            'waiters': waiters_data,
            'delivery-guys': delivery_guys_data,
            'cashiers': cashiers_data
        }

        sanitized_data = self.replace_invalid_floats(response_data)

        return Response(sanitized_data)

@permission_classes([IsAuthenticated])
class GeneralDataKdsViewSet(APIView):


    def replace_invalid_floats(self, data):
        """Recursively replace invalid float values with None."""
        if isinstance(data, dict):
            return {k: self.replace_invalid_floats(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.replace_invalid_floats(item) for item in data]
        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return None  # or return "NaN" / "Infinity" / "-Infinity" as strings if you prefer
        return data

    def get(self, request):
        categories = Category.objects.filter(parent__isnull=True, is_displayed=True)
        order_types = CmOrderType.objects.all()

        categories_data = CategorySerializer(categories, many=True).data
        order_types_data = CmOrderTypeKdsSerializer(order_types, many=True).data

        data = {
            'categories': categories_data,
            'order-types': order_types_data
        }

        response_data = self.replace_invalid_floats(data)

        return Response(response_data)

@permission_classes([IsAuthenticated])
class CmDaysViewSet(viewsets.ModelViewSet):
    queryset = CmDays.objects.all()
    serializer_class = CmDaysSerializer


    @action(detail=False, methods=['get'])
    def get_revenue(self, request):
        try:
            open_day = CmDays.objects.get(status="Open")
            # Calculate the total revenue for the open day by summing the revenue for all shifts in the day
            total_revenue = CmPayments.objects.filter(cm_shift__cm_day=open_day).aggregate(
                total=Sum('amount')
            )['total'] or 0.0

            return Response({
                "day_id": open_day.id,
                "total_revenue": total_revenue
            }, status=status.HTTP_200_OK)

        except CmDays.DoesNotExist:
            return Response({"error": "No open day found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def check_open_days(self, request):
        open_days = CmDays.objects.filter(status="Open")
        if open_days.exists():
            return Response({"message": "There are open days", "status": True}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No open days found", "status": False}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        data = request.data
        logger.debug(f"Request data received: {data}")
        opening_employee = data.get('opening_employee')

        if not opening_employee:
            return Response({"error": "opening_employee is a required field"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            opening_employee = CmEmployees.objects.get(id=opening_employee)
        except CmEmployees.DoesNotExist:
            return Response({"error": "Invalid opening_employee ID"}, status=status.HTTP_400_BAD_REQUEST)
        if CmDays.objects.filter(status="open").exists():
            return Response({"error": "There is already an open day. Please close it before opening a new day."}, status=status.HTTP_400_BAD_REQUEST)

        day = CmDays(
            name=f"Journée {date.today()}",
            opening_time=timezone.now(),
            closing_time=None,  # None by default
            status="Open",
            opening_employee=opening_employee,
            closing_employee=None,  # None by default
            revenue_system=0.0,  # Initial revenue set to 0
            revenue_declared=0.0  # Initial declared revenue set to 0
        )
        day.save()

        serializer = CmDaysSerializer(day)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def close_day(self, request):
        data = request.data
        closing_employee = data.get('closing_employee')

        if not closing_employee:
            return Response({"error": "closing_employee is a required field"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the open day
            open_day = CmDays.objects.get(status="Open")

            # Check if there are any open shifts for the current day
            open_shifts = CmShifts.objects.filter(cm_day=open_day, status="Open")
            if open_shifts.exists():
                return Response(
                    {"error": "All shifts must be closed before closing the day."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                # Update all is_displayed == True KDS orders to False
                CmKdsOrder.objects.filter(is_displayed=True).update(is_displayed=False)

                # Close the day
                open_day.date_end = timezone.now()
                open_day.closing_employee_id = closing_employee  # Ensure you are setting the ID
                open_day.status = "Closed"
                open_day.revenue_system = open_day.revenueSystem  # Calculating system revenue
                open_day.revenue_declared = open_day.revenueDeclared  # Calculating declared revenue
                open_day.save()

            serializer = CmDaysSerializer(open_day)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except CmDays.DoesNotExist:
            return Response({"error": "No open day found to close"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Failed to close day: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@permission_classes([IsAuthenticated])
class CmPosViewSet(viewsets.ModelViewSet):
    queryset = CmPos.objects.all()
    serializer_class = CmPosSerializer

@permission_classes([IsAuthenticated])
class CmTableViewSet(viewsets.ModelViewSet):
    queryset = CmTable.objects.all()
    serializer_class = CmTableSerializer

@permission_classes([IsAuthenticated])
class CmShiftsViewSet(viewsets.ModelViewSet):
    queryset = CmShifts.objects.all()
    serializer_class = CmShiftsSerializer


    @action(detail=True, methods=['get'])
    def get_revenue(self, request, pk=None):
        try:
            shift = CmShifts.objects.get(id=pk)
            # Calculate the total revenue for the shift
            total_revenue = CmPayments.objects.filter(cm_order__cm_shift=shift).aggregate(
                total=Sum('amount')
            )['total'] or 0.0

            return Response({
                "shift_id": shift.id,
                "total_revenue": total_revenue
            }, status=status.HTTP_200_OK)

        except CmShifts.DoesNotExist:
            return Response({"error": "Shift not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def by_day(self, request):
        day_id = request.query_params.get('day_id', None)
        if day_id is not None:
            shifts = CmShifts.objects.filter(cm_day_id=day_id)
            serializer = self.get_serializer(shifts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "day_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['post'])
    def open_shift(self, request):
        logger.debug(f"Request data received: {request.data}")
        cm_pos_id = request.data.get('cm_pos')
        cm_employee_id = request.data.get('cm_employee')
        starting_balance = request.data.get('starting_balance')
        
        if not cm_pos_id or not cm_employee_id or starting_balance is None:
            return Response({"error": f"cm_pos, cm_employee, and starting_balance are required.{request.data}"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cm_pos = CmPos.objects.get(id=cm_pos_id)
            cm_employee = CmEmployees.objects.get(id=cm_employee_id)
            cm_day = CmDays.objects.get(status="Open")
        except CmPos.DoesNotExist:
            return Response({"error": "CmPos not found."}, status=status.HTTP_404_NOT_FOUND)
        except CmEmployees.DoesNotExist:
            return Response({"error": "CmEmployee not found."}, status=status.HTTP_404_NOT_FOUND)
        except CmDays.DoesNotExist:
            return Response({"error": "No open day found."}, status=status.HTTP_404_NOT_FOUND)
        
        cm_shift = CmShifts.objects.create(
            cm_day=cm_day,
            cm_pos=cm_pos,
            cm_employee=cm_employee,
            opening_time=timezone.now(),
            starting_balance=starting_balance,
            status='Open'
        )
        serializer = CmShiftsSerializer(cm_shift)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def close_shift(self, request):
        data = request.data
        shift_id = data.get('shift_id')
        closing_amounts = data.get('closing_amounts', [])
        next_cashier_id = data.get('next_cashier')

        if not shift_id or not closing_amounts:
            return Response({"error": "shift_id and closing_amounts are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            shift = CmShifts.objects.get(id=shift_id, status="Open")

            # Check for non-paid orders
            unpaid_orders = CmOrders.objects.filter(cm_shift=shift, status="New").exists()

            if unpaid_orders:
                if not next_cashier_id:
                    return Response({"error": "Cannot close the shift while orders are still not paid. Please provide a next_cashier."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Create new shift for next_cashier
                    next_cashier = CmEmployees.objects.get(id=next_cashier_id)
                    new_shift = CmShifts.objects.create(
                        cm_day=shift.cm_day,
                        cm_pos=shift.cm_pos,
                        cm_employee=next_cashier,
                        opening_time=timezone.now(),
                        starting_balance=0.0,
                        status='opening_control'
                    )
                    # Return a message indicating the new shift creation
                    # return Response({"message": f"New shift created for {next_cashier.name} with status 'opening_control' due to unpaid orders."}, status=status.HTTP_200_OK)

            with transaction.atomic():
                # Process each payment method's closing balance
                for closing_data in closing_amounts:
                    payment_method_id = closing_data.get('cm_payment_method')
                    cashier_amount = closing_data.get('cashier_amount')

                    if not payment_method_id or cashier_amount is None:
                        return Response({"error": "Each closing_amount entry must have cm_payment_method and cashier_amount."}, status=status.HTTP_400_BAD_REQUEST)

                    # Fetch the payment method and check if it's cash
                    payment_method = CmPaymentMethods.objects.get(id=payment_method_id)
                    is_cash = payment_method.is_cash

                    # Calculate the system amount
                    system_amount = CmPayments.objects.filter(cm_order__cm_shift=shift, cm_payment_method_id=payment_method_id).aggregate(
                        total_amount=Sum('amount')
                    )['total_amount'] or 0.0

                    # If the payment method is cash, include drops and subtract starting balance
                    if is_cash:
                        total_drops = CmDrops.objects.filter(cm_shift=shift).aggregate(
                            total_drops=Sum('amount')
                        )['total_drops'] or 0.0

                        cashier_amount += total_drops - shift.starting_balance

                    # Create the closing balance entry
                    CmClosingBalances.objects.create(
                        cm_payment_method_id=payment_method_id,
                        cm_shift=shift,
                        system_amount=system_amount,
                        cashier_amount=cashier_amount,
                        verification_amount=0.0,  # Assuming 0 for now
                        verification_employee=None  # Assuming None for now
                    )

                shift.status = "Closed"
                shift.closing_time = timezone.now()
                shift.save()

            serializer = CmShiftsSerializer(shift)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except CmShifts.DoesNotExist:
            return Response({"error": "Open shift not found."}, status=status.HTTP_404_NOT_FOUND)
        except CmEmployees.DoesNotExist:
            return Response({"error": "Next cashier not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Failed to close shift: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['post'])
    def update_shift(self, request):
        data = request.data
        shift_id = data.get('shift_id')
        starting_balance = data.get('starting_balance')

        if not shift_id or starting_balance is None:
            return Response({"error": "shift_id and starting_balance are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the shift with status 'opening_control'
            shift = CmShifts.objects.get(id=shift_id, status="opening_control")

            # Update shift details
            shift.starting_balance = starting_balance
            shift.status = "Open"
            shift.opening_time = timezone.now()
            shift.save()

            serializer = CmShiftsSerializer(shift)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except CmShifts.DoesNotExist:
            return Response({"error": "Shift not found or not in 'opening_control' status."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Failed to update shift: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@permission_classes([IsAuthenticated])
class CmFloorViewSet(viewsets.ModelViewSet):
    queryset = CmFloor.objects.all()
    serializer_class = CmFloorSerializer
