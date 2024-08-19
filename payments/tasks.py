from .models import CmPayments, CmOrders, CmPaymentMethods
from django.db import transaction

def process_payment_sync(payment_data):
    with transaction.atomic():
        cm_order_id = payment_data.get('cm_order')
        amount = payment_data.get('amount')
        cm_payment_method_id = payment_data.get('cm_payment_method')

        cm_order = CmOrders.objects.get(id=cm_order_id)
        cm_payment_method = CmPaymentMethods.objects.get(id=cm_payment_method_id)

        # Create the payment record
        payment = CmPayments.objects.create(
            cm_order=cm_order,
            amount=amount,
            cm_payment_method=cm_payment_method,
            status='paid'
        )

        # Verify if the order is fully paid
        total_paid = sum(p.amount for p in cm_order.payments.all())
        if round(total_paid, 2) >= round(cm_order.total_amount, 2):
            cm_order.status = 'Paid'
            cm_order.save()

    return payment.id
