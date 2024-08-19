import logging
import json
import datetime
import asyncio
from uuid import uuid4  # Import UUID for group_id
from .models import CmOrderLine, CmOrders
from kds.models import CmKdsOrder, CmKdsOrderline
from server.settings import socket_server_url
from products.models import KitchenPoste, ProductVariant
import requests

logger = logging.getLogger(__name__)

def process_kitchen_display(order_id):
    try:
        # Fetch orderlines related to the order
        orderlines = CmOrderLine.objects.filter(order_id=order_id).select_related('product_variant', 'order')

        # Check if orderlines are fetched
        if not orderlines.exists():
            logger.error(f"No orderlines found for order {order_id}")
            return

        # Get the order object from the first orderline (assuming all orderlines belong to the same order)
        order = orderlines[0].order
        logger.info(f"Processing kitchen display for order {order_id}, order ref: {order.ref}")

        # Generate a unique group_id for this batch of KDS orders
        group_id = uuid4()

        # Dictionaries for kitchen postes
        kitchen_poste_dict = {}

        # Process each orderline
        for orderline in orderlines:
            product_variant = orderline.product_variant

            # Fetch related kitchen postes
            kitchen_postes = KitchenPoste.objects.filter(product_variants=product_variant).prefetch_related('screen_poste')
            for kitchen_poste in kitchen_postes:
                if kitchen_poste.id not in kitchen_poste_dict:
                    kitchen_poste_dict[kitchen_poste.id] = {"poste": kitchen_poste, "orderlines": []}
                kitchen_poste_dict[kitchen_poste.id]["orderlines"].append(orderline)

        # Handle printers and screens
        handle_printers(kitchen_poste_dict)
        handle_kds(kitchen_poste_dict, order, group_id)

    except Exception as e:
        logger.error(f"Error processing kitchen display for order {order_id}: {str(e)}")


def process_kitchen_display_for_new_lines(order_id, new_order_lines):
    try:
        order = CmOrders.objects.get(id=order_id)
        logger.info(f"Processing kitchen display for new lines in order {order_id}, order ref: {order.ref}")

        # Generate a unique group_id for this batch of KDS orders
        group_id = uuid4()

        # Dictionaries for kitchen postes
        kitchen_poste_dict = {}

        # Process each new orderline
        for orderline in new_order_lines:
            product_variant = orderline.product_variant

            # Fetch related kitchen postes
            kitchen_postes = KitchenPoste.objects.filter(product_variants=product_variant).prefetch_related('screen_poste')
            for kitchen_poste in kitchen_postes:
                if kitchen_poste.id not in kitchen_poste_dict:
                    kitchen_poste_dict[kitchen_poste.id] = {"poste": kitchen_poste, "orderlines": []}
                kitchen_poste_dict[kitchen_poste.id]["orderlines"].append(orderline)

        # Handle printers and screens
        handle_printers(kitchen_poste_dict)
        handle_kds(kitchen_poste_dict, order, group_id)

    except Exception as e:
        logger.error(f"Error processing kitchen display for new lines in order {order_id}: {str(e)}")


def handle_printers(kitchen_poste_dict):
    for poste_id, data in kitchen_poste_dict.items():
        kitchen_poste = data["poste"]
        orderlines = data["orderlines"]
        if kitchen_poste.by_ip:
            logger.info(f"Sending to printer: {kitchen_poste.name}")
            for orderline in orderlines:
                logger.info(f"Orderline for printer: {orderline}")


def handle_kds(kitchen_poste_dict, order, group_id):
    # List to collect data for each kitchen poste
    kitchen_poste_data_list = []

    for poste_id, data in kitchen_poste_dict.items():
        kitchen_poste = data["poste"]
        orderlines = data["orderlines"]

        # Add checks to ensure related objects are not None
        if not kitchen_poste.screen_poste:
            logger.error(f"Screen poste is None for kitchen poste {kitchen_poste.name}")
            continue

        first_stage = kitchen_poste.screen_poste.stage_ids.order_by('sequence').first()
        if not first_stage:
            logger.error(f"No stages found for preparation display {kitchen_poste.screen_poste.name}")
            continue

        # Create KDS order
        kds_order = CmKdsOrder.objects.create(
            cm_pos_order=order,
            cm_preparation_display=kitchen_poste.screen_poste,
            cm_preparation_display_stage=first_stage,
            sequence=0,
            group_id=group_id  # Assign the group_id to the KDS order
        )

        logger.info(f"KDS order created with ID {kds_order.id}")

        # Create KDS order lines
        kds_orderlines = create_kds_orderlines(orderlines, kds_order, kitchen_poste)

        # Prepare data for socket communication for this kitchen poste
        kitchen_poste_data = {
            "kitchen_poste": kitchen_poste.name,
            "preparation_display_id": kitchen_poste.screen_poste.id,
            "kds_order": prepare_kds_order_data(order, kds_order, kds_orderlines)
        }

        # Add this kitchen poste data to the list
        kitchen_poste_data_list.append(kitchen_poste_data)

    # Send the full list of kitchen poste data to the socket
    send_order_to_socket(kitchen_poste_data_list)


def create_kds_orderlines(orderlines, kds_order, kitchen_poste):
    kds_orderlines = []
    for orderline in orderlines:
        # Get the set of combo_prod_ids that are linked to the current kitchen_poste
        relevant_combo_prod_ids = kitchen_poste.product_variants.filter(
            id__in=orderline.combo_prods.values_list('id', flat=True)
        )

        # Create KDS order line with filtered combo_prod_ids
        kds_orderline = CmKdsOrderline.objects.create(
            cm_kds_order=kds_order,
            cm_pos_orderline=orderline,
            suiteCommande=orderline.suite_commande,
            suiteOrdred=orderline.suite_ordred
        )

        # Add the relevant combo_prod_ids to the kds_orderline
        kds_orderline.combo_prod_ids.add(*relevant_combo_prod_ids)

        # Append filtered combo_prod_ids to kds_orderline data to be used in the socket data preparation
        kds_orderline.filtered_combo_prod_ids = list(relevant_combo_prod_ids.values_list('name', flat=True))

        kds_orderlines.append(kds_orderline)
    
    return kds_orderlines


def prepare_kds_order_data(order, kds_order, kds_orderlines):
    order_data = {
        "id": kds_order.id,
        "pos_order_id": order.id,
        "stage_id": kds_order.cm_preparation_display_stage.id,
        "table": kds_order.cm_pos_order.cm_table.name if kds_order.cm_pos_order.cm_table else None,
        "waiter": kds_order.cm_pos_order.cm_waiter.name if kds_order.cm_pos_order.cm_waiter else None,
        "orderType": kds_order.cm_pos_order.cm_order_type.id,
        "ref": kds_order.cm_pos_order.ref,
        "customer_count": kds_order.cm_pos_order.customer_count,
        "create_date": str(kds_order.create_at),
        "orderlines": []
    }

    # Loop through each order line
    for orderline in kds_orderlines:
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
            # Use the filtered combo_prod_ids that were set during creation
            "combo_prod_ids": orderline.filtered_combo_prod_ids  
        }
        order_data["orderlines"].append(orderline_data)

    return order_data


def send_order_to_socket(kitchen_poste_data_list):
    uri = socket_server_url + "/send-order"  # Correct API URL
    try:
        logger.info(f"Sending order data to {uri}")
        response = requests.post(uri, json=kitchen_poste_data_list)
         
        if response.status_code == 200:
            logger.info("Order data successfully sent to the socket service")
        else:
            logger.error(f"Failed to send order data, status code: {response.status_code}, response: {response.text}")
    except Exception as e:
        logger.error(f"Failed to send order data to the socket service: {str(e)}")
