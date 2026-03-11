from google.adk.tools.tool_context import ToolContext


def get_parts_from_pcpartpicker(tool_context: ToolContext, url: str) -> dict:
    """
    Fetch and load the user's parts list from a PC Part Picker URL.

    Use this when the user shares their PC Part Picker link at the start
    of a build session. This initializes build tracking for all parts.
    Only call this once per session.

    Args:
        url: The PC Part Picker list URL (e.g. https://pcpartpicker.com/list/abc123)
    """

    # mocking the response for demo
    parts = {
        "cpu": {
            "name": "AMD Ryzen 5 5600X 3.7 GHz 6-Core Processor",
            "category": "CPU",
        },
        "cooler": {
            "name": "Noctua NH-U12S 55 CFM CPU Cooler",
            "category": "CPU Cooler",
        },
        "motherboard": {
            "name": "Asus TUF GAMING X570-PLUS (WI-FI) ATX AM4 Motherboard",
            "category": "Motherboard",
        },
        "ram": {
            "name": "G.Skill Ripjaws V 32 GB (2 x 16 GB) DDR4-3200 CL16 Memory",
            "category": "Memory",
        },
        "storage": {
            "name": "Crucial T500 1 TB M.2-2280 PCIe 4.0 X4 NVME Solid State Drive",
            "category": "Storage",
        },
        "gpu": {
            "name": "Gigabyte AORUS ELITE GeForce RTX 3060 Ti 8 GB Video Card",
            "category": "Video Card",
        },
        "case": {
            "name": "Corsair 4000D Airflow ATX Mid Tower Case",
            "category": "Case",
        },
        "psu": {
            "name": "EVGA SuperNOVA 750 GA 750 W 80+ Gold Certified Fully Modular ATX Power Supply",
            "category": "Power Supply",
        },
        "monitor": {
            "name": 'LG 24GL600F-B 23.6" 1920 x 1080 144 Hz Monitor',
            "category": "Monitor",
        },
    }

    # init build_progress with status
    build = {
        part_id: {
            "name": info["name"],
            "category": info["category"],
            "status": "NOT_STARTED",
            "notes": "",
        }
        for part_id, info in parts.items()
    }
    tool_context.state["build_progress"] = build
    return {
        "status": "success",
        "total_parts": len(build),
        "parts": [
            {"id": id, "name": info["name"], "category": info["category"]}
            for id, info in parts.items()
        ],
    }


def get_compatibility_warnings() -> dict:
    """
    Check for known compatibility issues with the current build.

    Use this after parts are loaded via get_parts_from_pcpartpicker, or
    when the user begins working on a component that may have a known issue.
    Proactively warn the user before they start installing an affected part.
    """
    # mockpcpartpicker
    return {
        "status": "success",
        "warnings": [
            {
                "severity": "warning",
                "parts": ["motherboard", "cpu"],
                "message": (
                    "The Asus TUF GAMING X570-PLUS (WI-FI) supports the Ryzen 5 5600X "
                    "only with BIOS version 2607 or newer. If the board ships with an "
                    "older BIOS, it will need to be updated before the CPU will POST."
                ),
            },
            {
                "severity": "note",
                "parts": ["motherboard", "case"],
                "message": "A USB 2.0 to USB 3.2 Gen 1 header adapter is required.",
            },
            {
                "severity": "note",
                "parts": ["motherboard", "case"],
                "message": "A USB 3.2 Gen 1 to USB 3.2 Gen 2 header adapter is required.",
            },
            {
                "severity": "note",
                "parts": ["cooler", "motherboard"],
                "message": (
                    "The Noctua NH-U12S may require a separately available mounting "
                    "adapter to fit the AM4 socket on this motherboard."
                ),
            },
            {
                "severity": "disclaimer",
                "parts": ["cooler", "ram"],
                "message": (
                    "Physical constraints like RAM clearance with the CPU cooler "
                    "are not verified. Check that the NH-U12S does not interfere "
                    "with the G.Skill Ripjaws V in slots A2/B2."
                ),
            },
        ],
    }


def fetch_mobo_info(tool_context: ToolContext) -> dict:
    # TODO: either vectorize the manual, or hardcode for demo
    return {
        "status": "success",
        "info": "Front Panel Headers: The layout for this specific board is: Top row (PLED+, PLED-, PWRBTN, Ground), Bottom row (HDLED+, HDLED-, RESET, Ground)",
    }


def show_user_part(part_category: str) -> dict:
    """
    Called to display a photo of the user's specific hardware component.

    Args:
        part_category: The specific component to show. Must be one of: 'cpu', 'motherboard', 'ram', 'gpu', 'cooler', 'psu', 'case', 'storage'
    """
    inventory_images = {
        "cpu": "https://cdna.pcpartpicker.com/static/forever/images/product/3ef757133d38ac40afe75da691ba7d60.256p.jpg",
        "motherboard": "https://cdna.pcpartpicker.com/static/forever/images/product/8d7d0435e8a2af93b5d91a1a5dccd476.256p.jpg",
        "ram": "https://cdna.pcpartpicker.com/static/forever/images/product/f97fce0b44ff2447a790b0bffc74f9f3.256p.jpg",
        "gpu": "https://cdna.pcpartpicker.com/static/forever/images/product/0c5f0e5e6cd671133808843a5f9236bb.256p.jpg",
        "cooler": "https://cdna.pcpartpicker.com/static/forever/images/product/351c9a441cd970d83faee6f581d07f73.med.256p.jpg",
        "psu": "https://m.media-amazon.com/images/I/51zNwtqLpuL.jpg",
        "case": "https://cdna.pcpartpicker.com/static/forever/images/product/bc6e987da3fe22c616898d1d7fa3d227.256p.jpg",
        "storage": "https://cdna.pcpartpicker.com/static/forever/images/product/3fd5aee2fd8854d15ef3c81dcd9599f5.256p.jpg",
    }

    if part_category not in inventory_images:
        return {"status": "error", "error_message": "Image not found for this part."}

    return {"status": "success", "image_url": inventory_images[part_category]}


# pc_part_picker_txt = """
# PCPartPicker Part List: https://pcpartpicker.com/list/n3Gkt3
#
# CPU: AMD Ryzen 5 5600X 3.7 GHz 6-Core Processor  ($163.00 @ Amazon)
# CPU Cooler: Noctua NH-U12S 55 CFM CPU Cooler  ($84.95 @ Amazon)
# Motherboard: Asus TUF GAMING X570-PLUS (WI-FI) ATX AM4 Motherboard
# Memory: G.Skill Ripjaws V 32 GB (2 x 16 GB) DDR4-3200 CL16 Memory  ($284.99 @ Amazon)
# Storage: Crucial T500 1 TB M.2-2280 PCIe 4.0 X4 NVME Solid State Drive  ($197.99 @ Amazon)
# Video Card: Gigabyte AORUS ELITE GeForce RTX 3060 Ti 8 GB Video Card
# Case: Corsair 4000D Airflow ATX Mid Tower Case
# Power Supply: EVGA SuperNOVA 750 GA 750 W 80+ Gold Certified Fully Modular ATX Power Supply
# Monitor: LG 24GL600F-B 23.6" 1920 x 1080 144 Hz Monitor  ($189.99 @ LG - OOS)
# Total: $920.92
# Prices include shipping, taxes, and discounts when available
# Generated by PCPartPicker 2026-03-02 12:33 EST-0500"""
#
#
