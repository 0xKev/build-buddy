import json
from pathlib import Path

_DIR = Path(__file__).parent
CONNECTORS = {}

# load connectors.json into memory
with open(_DIR / "connectors.json") as f:
    data = json.load(f)

    for category in data["categories"].values():
        for entry in category["entries"]:
            CONNECTORS[entry["id"]] = {
                "url": entry["url"],
                "description": entry["description"],
            }


def get_connector_image(connector_id: str) -> dict:
    """Get the reference image URL for a PC connector/port.

    Args:
        connector_id: The connector identifier. Valid IDs:
            ATX Power: 24pin_atx_socket, 24pin_atx_plug, 4pin_atx_socket, 4pin_atx_plug
            EPS Power: 8pin_eps_socket, 8pin_eps_plug
            PCIe Power: 6pin_pcie_socket, 6pin_pcie_plug, 6p2pin_pcie_plug,
                8pin_pcie_socket, 8pin_pcie_plug, 12pin_pcie,
                16pin_pcie_gen5_socket, 16pin_pcie_gen5_plug
            Peripheral: 4pin_molex, molex_power, sata_power_socket, sata_power_plug
            Data: sata_data, ide, u2
            PCIe Slots: pcie_x1, pcie_x4, pcie_x8, pcie_x16, pci, pci_x, mini_pcie
            M.2: m2_m_key, m2_b_key, m2_e_key
            CPU: amd_am1, amd_am2, amd_am4, amd_fm1, amd_fm2, amd_str4,
                intel_lga1150, intel_lga1356, intel_lga1700, intel_lga2011, intel_lga2066
            Memory: ddr4
            USB Headers: usb3_gen1, usb3_gen2, usb_header

    Returns:
        Dict with 'url' and 'description', or error with valid_ids list.
    """
    result = CONNECTORS.get(connector_id)
    if result:
        return {
            "status": "success",
            "connector_url": result["url"],
            "description": result["description"],
        }
    return {
        "error_message": f"no reference image available for connector {connector_id}"
    }
