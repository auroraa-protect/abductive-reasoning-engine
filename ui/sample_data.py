"""
Sample test cases for Auroraa Abductive Reasoning Engine UI.
Contains preloaded industry scenarios including the standard ABC Textile Industries test case.
"""

import json
from typing import Dict, Any

ABC_TEXTILE_DATA: Dict[str, Any] = {
    "business_profile": {
        "business_name": "ABC Textile Industries",
        "business_type": "manufacturing",
        "industry": "textile",
        "business_activity": "Cotton fabric manufacturing",
        "business_age_years": 5,
        "declared_monthly_turnover": 1500000,
        "declared_monthly_production": 8000,
        "declared_production_capacity": 10000,
        "number_of_employees": 15,
    },
    "purchase_evidence": {
        "bills": [
            {
                "supplier_name": "XYZ Cotton Traders",
                "invoice_date": "2026-10-01",
                "items": [
                    {
                        "item_name": "Raw Cotton",
                        "quantity": 1000,
                        "unit": "kg",
                        "unit_price": 150,
                        "total_amount": 150000,
                    }
                ],
                "total_amount": 150000,
            }
        ]
    },
    "inventory_evidence": {
        "declared_inventory": [
            {
                "item_name": "Raw Cotton",
                "quantity": 500,
                "unit": "kg",
                "estimated_value": 75000,
            },
            {
                "item_name": "Finished Fabric",
                "quantity": 2000,
                "unit": "meters",
                "estimated_value": 300000,
            },
        ],
        "image_analysis": [
            {
                "observed_objects": [
                    {
                        "object": "Cotton storage bags",
                        "estimated_count": 20,
                        "confidence": 0.91,
                    },
                    {
                        "object": "Fabric rolls",
                        "estimated_count": 35,
                        "confidence": 0.94,
                    },
                ],
                "observations": [
                    "Cotton storage bags observed",
                    "Finished fabric rolls observed",
                    "Inventory stored inside warehouse",
                ],
                "analysis_confidence": 0.89,
            }
        ],
    },
    "production_evidence": {
        "production_records": [
            {
                "date": "2026-10-15",
                "product": "Cotton Fabric",
                "quantity": 8000,
                "unit": "meters",
            }
        ],
        "raw_material_consumption": [
            {"material": "Raw Cotton", "quantity": 1600, "unit": "kg"}
        ],
        "finished_goods": [
            {
                "product": "Cotton Fabric",
                "quantity": 8000,
                "unit": "meters",
            }
        ],
    },
    "sales_evidence": {
        "sales_bills": [
            {
                "customer_name": "ABC Garments",
                "invoice_date": "2026-10-20",
                "total_amount": 250000,
            }
        ],
        "customer_details": [
            {"customer_name": "ABC Garments", "relationship": "Retailer"}
        ],
        "sales_summary": {"total_sales_value": 250000, "period": "2026-10"},
    },
    "physical_evidence": {
        "video_analysis": [
            {
                "duration_seconds": 120,
                "observed_activities": [
                    "Workers operating textile machinery",
                    "Fabric processing activity",
                ],
                "observed_machinery": ["Power loom", "Fabric cutting machine"],
                "observations": [
                    "Manufacturing activity visible",
                    "Multiple workers present",
                ],
                "analysis_confidence": 0.88,
            }
        ],
        "machinery_analysis": [
            {
                "machine_name": "Power Loom",
                "observed_count": 5,
                "condition": "Operational",
            }
        ],
        "premises_analysis": [
            {
                "area": "Production floor",
                "observation": "Manufacturing equipment and fabric rolls observed",
            }
        ],
    },
    "financial_evidence": {
        "bank_transactions": [
            {
                "transaction_date": "2026-10-21",
                "transaction_type": "credit",
                "amount": 250000,
                "description": "ABC Garments payment",
            }
        ],
        "electricity_bills": [
            {
                "billing_month": "2026-10",
                "units_consumed": 4500,
                "bill_amount": 38000,
            }
        ],
        "gst_records": [{"period": "2026-10", "declared_turnover": 1500000}],
    },
    "additional_evidence": {
        "documents": [],
        "observations": [
            "Business claims monthly production capacity of 10000 meters"
        ],
    },
}

SUNRISE_TRADING_DATA: Dict[str, Any] = {
    "business_profile": {
        "business_name": "Sunrise Electronics Trading",
        "business_type": "trading",
        "industry": "electronics",
        "business_activity": "Wholesale distribution of mobile accessories",
        "business_age_years": 4,
        "declared_monthly_turnover": 3000000,
        "number_of_employees": 6,
    },
    "purchase_evidence": {
        "bills": [
            {
                "supplier_name": "Global Tech Imports",
                "invoice_date": "2026-10-05",
                "items": [
                    {
                        "item_name": "Wireless Earbuds",
                        "quantity": 2000,
                        "unit": "pcs",
                        "unit_price": 600,
                        "total_amount": 1200000,
                    },
                    {
                        "item_name": "Fast Chargers",
                        "quantity": 5000,
                        "unit": "pcs",
                        "unit_price": 200,
                        "total_amount": 1000000,
                    },
                ],
                "total_amount": 2200000,
            }
        ]
    },
    "sales_evidence": {
        "sales_bills": [
            {
                "customer_name": "Retail Hub Delhi",
                "invoice_date": "2026-10-18",
                "total_amount": 1500000,
            },
            {
                "customer_name": "Metro Gadgets",
                "invoice_date": "2026-10-24",
                "total_amount": 1200000,
            },
        ],
        "sales_summary": {"total_sales_value": 2700000, "period": "2026-10"},
    },
    "financial_evidence": {
        "bank_transactions": [
            {
                "transaction_date": "2026-10-20",
                "transaction_type": "credit",
                "amount": 1500000,
                "description": "Retail Hub NEFT payment",
            },
            {
                "transaction_date": "2026-10-26",
                "transaction_type": "credit",
                "amount": 1200000,
                "description": "Metro Gadgets RTGS payment",
            },
        ],
        "gst_records": [{"period": "2026-10", "declared_turnover": 2700000}],
    },
    "physical_evidence": {
        "premises_analysis": [
            {
                "area": "Warehouse",
                "observation": "Packaged mobile accessories and retail shipping boxes stacked on pallet racks",
            }
        ]
    },
}

APEX_SERVICES_DATA: Dict[str, Any] = {
    "business_profile": {
        "business_name": "Apex Software Consulting",
        "business_type": "service",
        "industry": "information_technology",
        "business_activity": "Enterprise cloud consulting and software engineering",
        "business_age_years": 3,
        "declared_monthly_turnover": 1000000,
        "number_of_employees": 8,
    },
    "sales_evidence": {
        "sales_bills": [
            {
                "customer_name": "FinCorp Inc",
                "invoice_date": "2026-10-01",
                "total_amount": 660000,
            },
            {
                "customer_name": "HealthCare Solutions Ltd",
                "invoice_date": "2026-10-02",
                "total_amount": 250000,
            },
        ],
        "sales_summary": {"total_sales_value": 910000, "period": "2026-10"},
    },
    "financial_evidence": {
        "bank_transactions": [
            {
                "transaction_date": "2026-10-05",
                "transaction_type": "credit",
                "amount": 660000,
                "description": "Wire from FinCorp Inc - Retainer",
            },
            {
                "transaction_date": "2026-10-07",
                "transaction_type": "credit",
                "amount": 250000,
                "description": "Wire from HealthCare Solutions Ltd - Milestone 2",
            },
        ],
        "electricity_bills": [
            {
                "billing_month": "2026-10",
                "units_consumed": 750,
                "bill_amount": 6200,
            }
        ],
        "gst_records": [{"period": "2026-10", "declared_turnover": 910000}],
    },
    "physical_evidence": {
        "premises_analysis": [
            {
                "area": "Office",
                "observation": "1,200 sq ft office in IT park with 8 dual-monitor workstations occupied by developers",
            }
        ]
    },
}

SAMPLE_TEXT_NARRATIVE = """ABC Textile Industries is a 5-year-old cotton fabric manufacturer located in Surat, Gujarat.
The business claims a declared monthly turnover of ₹15 Lakhs, declared monthly production of 8,000 meters, and total capacity of 10,000 meters/month with 15 workers.

Documentary and Physical Evidence:
1. Purchase bill PUR-001 from XYZ Cotton Traders for 1,000 kg Raw Cotton at ₹150/kg (Total: ₹1,50,000).
2. Production log shows 1,600 kg of raw cotton consumed to produce 8,000 meters of finished fabric.
3. Sales bill SALE-001 shows ₹2,50,000 sold to ABC Garments.
4. Bank statement shows a corresponding credit deposit of ₹2,50,000 from ABC Garments.
5. On-site video inspection VID-001 verifies 5 operational power looms running with active workers and fabric rolls in warehouse.
6. Electricity bill shows 4,500 units consumed (₹38,000).
7. GST return for October 2026 shows declared turnover of ₹15 Lakhs."""

SAMPLE_CASES = {
    "ABC Textile Industries (Manufacturing - Standard Test Case)": {
        "industry": "Manufacturing",
        "description": "MSME cotton fabric manufacturer in Surat with 5 operational power looms, 15 workers, and capacity of 10,000 m/month.",
        "data": ABC_TEXTILE_DATA,
        "json_str": json.dumps(ABC_TEXTILE_DATA, indent=2),
        "text_narrative": SAMPLE_TEXT_NARRATIVE,
    },
    "Sunrise Electronics Trading (Wholesale Distribution)": {
        "industry": "Trading",
        "description": "Wholesale distributor of mobile phone accessories and fast chargers supplying retail electronics stores.",
        "data": SUNRISE_TRADING_DATA,
        "json_str": json.dumps(SUNRISE_TRADING_DATA, indent=2),
        "text_narrative": (
            "Sunrise Electronics Trading is a wholesale distributor of mobile accessories in Delhi. "
            "Declared monthly turnover is ₹30 Lakhs with 6 employees. "
            "Documented purchases show ₹22 Lakhs from Global Tech Imports (2,000 earbuds, 5,000 fast chargers). "
            "Documented sales invoices total ₹27 Lakhs to Retail Hub and Metro Gadgets. "
            "Bank statements show ₹27 Lakhs incoming credits matching sales collections. "
            "Warehouse inspection confirms boxed stock matching these categories."
        ),
    },
    "Apex Software Consulting (IT Services)": {
        "industry": "Services",
        "description": "Custom enterprise software engineering firm with 8 software engineers and 1,200 sq ft office in IT park.",
        "data": APEX_SERVICES_DATA,
        "json_str": json.dumps(APEX_SERVICES_DATA, indent=2),
        "text_narrative": (
            "Apex Software Consulting provides custom web development and enterprise cloud consulting in Bengaluru. "
            "Declared monthly revenue is ₹10 Lakhs with 8 full-time software engineers. "
            "Active client retainers: FinCorp Inc (₹6.6 Lakhs) and HealthCare Solutions Ltd (₹2.5 Lakhs), totaling ₹9.1 Lakhs. "
            "Bank statements show matching credits of ₹9.1 Lakhs. "
            "Office lease shows 1,200 sq ft rented space with 8 active developer workstations."
        ),
    },
}

ABC_TEXTILE_JSON = json.dumps(ABC_TEXTILE_DATA, indent=2)
