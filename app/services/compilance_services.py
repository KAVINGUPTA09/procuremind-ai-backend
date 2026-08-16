from app.models.schemas import (
    RFQ,
    RFQItem,
    VendorQuotation,
    QuotationLineItem
)


def normalize_text(
    value: str
) -> str:
    """
    Normalizes text for comparison.
    """

    return str(value).strip().lower()


def find_vendor_item(
    rfq_item: RFQItem,
    vendor_items: list[QuotationLineItem]
) -> QuotationLineItem | None:
    """
    Finds the matching vendor item.
    """

    rfq_name = normalize_text(
        rfq_item.item_name
    )

    for vendor_item in vendor_items:

        vendor_name = normalize_text(
            vendor_item.item_name
        )

        if rfq_name == vendor_name:
            return vendor_item

    return None


def compare_quantity(
    required_quantity: int,
    quoted_quantity: int
) -> bool:
    """
    Checks quantity.
    """

    return quoted_quantity >= required_quantity


def compare_delivery(
    required_delivery: int,
    vendor_delivery: int
) -> bool:
    """
    Checks delivery timeline.
    """

    return vendor_delivery <= required_delivery


def compare_warranty(
    required_warranty: int,
    vendor_warranty: int
) -> bool:
    """
    Checks warranty.
    """

    return vendor_warranty >= required_warranty


def compare_specifications(
    required_specifications: dict,
    vendor_specifications: dict
):
    """
    Compares every specification.
    """

    results = []

    overall_match = True

    for key, value in required_specifications.items():

        vendor_value = vendor_specifications.get(
            key
        )

        match = (
            normalize_text(value)
            ==
            normalize_text(vendor_value)
        )

        if not match:
            overall_match = False

        results.append(
            {
                "specification": key,
                "required": value,
                "vendor": vendor_value,
                "match": match
            }
        )

    return overall_match, results

def calculate_vendor_compliance(
    rfq: RFQ,
    vendor: VendorQuotation
) -> dict:
    """
    Compares the complete vendor quotation
    against the buyer RFQ.
    """

    total_checks = 0
    passed_checks = 0

    item_results = []

    # ---------------------------------------------------
    # Delivery Comparison
    # ---------------------------------------------------

    delivery_match = compare_delivery(
        rfq.required_delivery_days,
        vendor.delivery_days
    )

    total_checks += 1

    if delivery_match:
        passed_checks += 1

    # ---------------------------------------------------
    # Warranty Comparison
    # ---------------------------------------------------

    warranty_match = compare_warranty(
        rfq.required_warranty_months,
        vendor.warranty_months
    )

    total_checks += 1

    if warranty_match:
        passed_checks += 1

    # ---------------------------------------------------
    # Item Comparison
    # ---------------------------------------------------

    for rfq_item in rfq.items:

        vendor_item = find_vendor_item(
            rfq_item,
            vendor.line_items
        )

        # -----------------------------
        # Item Missing
        # -----------------------------

        if vendor_item is None:

            item_results.append(
                {
                    "item_name": rfq_item.item_name,
                    "item_found": False,
                    "quantity_match": False,
                    "specifications_match": False,
                    "specification_details": []
                }
            )

            total_checks += 3

            continue

        # -----------------------------
        # Item Found
        # -----------------------------

        total_checks += 1

        passed_checks += 1

        # -----------------------------
        # Quantity
        # -----------------------------

        quantity_match = compare_quantity(
            rfq_item.required_quantity,
            vendor_item.quoted_quantity
        )

        total_checks += 1

        if quantity_match:
            passed_checks += 1

        # -----------------------------
        # Specifications
        # -----------------------------

        (
            specifications_match,
            specification_details
        ) = compare_specifications(
            rfq_item.specifications,
            vendor_item.specifications
        )

        total_checks += 1

        if specifications_match:
            passed_checks += 1

        # -----------------------------
        # Store Result
        # -----------------------------

        item_results.append(
            {
                "item_name": rfq_item.item_name,

                "item_found": True,

                "required_quantity":
                    rfq_item.required_quantity,

                "quoted_quantity":
                    vendor_item.quoted_quantity,

                "quantity_match":
                    quantity_match,

                "specifications_match":
                    specifications_match,

                "specification_details":
                    specification_details
            }
        )

    # ---------------------------------------------------
    # Compliance %
    # ---------------------------------------------------

    if total_checks == 0:

        compliance_percentage = 0

    else:

        compliance_percentage = round(

            (
                passed_checks
                /
                total_checks
            )
            * 100,

            2
        )

    # ---------------------------------------------------
    # Final Report
    # ---------------------------------------------------

    report = {

        "vendor_name":
            vendor.vendor_name,

        "delivery_match":
            delivery_match,

        "required_delivery_days":
            rfq.required_delivery_days,

        "vendor_delivery_days":
            vendor.delivery_days,

        "warranty_match":
            warranty_match,

        "required_warranty_months":
            rfq.required_warranty_months,

        "vendor_warranty_months":
            vendor.warranty_months,

        "item_results":
            item_results,

        "passed_checks":
            passed_checks,

        "total_checks":
            total_checks,

        "compliance_percentage":
            compliance_percentage
    }

    return report