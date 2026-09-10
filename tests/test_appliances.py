"""
tests/test_appliances.py — Unit tests for appliance classification and spec extraction.
"""
import unittest

from core.appliances import (
    get_appliance_type,
    get_department_name,
    extract_generic_specs,
)


class TestApplianceClassification(unittest.TestCase):
    def test_air_conditioner_classification(self):
        self.assertEqual(
            get_appliance_type("Voltas 1.5 Ton 3 Star Inverter Split AC"),
            "❄️ Air Conditioners (AC)",
        )
        self.assertEqual(
            get_appliance_type("LG Window AC 1 Ton 5 Star"),
            "❄️ Air Conditioners (AC)",
        )

    def test_refrigerator_classification(self):
        self.assertEqual(
            get_appliance_type("Samsung 253 L 3 Star Frost Free Double Door Refrigerator"),
            "🧊 Refrigerators (Fridge)",
        )
        self.assertEqual(
            get_appliance_type("Whirlpool 190 L Single Door Direct Cool Fridge"),
            "🧊 Refrigerators (Fridge)",
        )

    def test_washing_machine_classification(self):
        self.assertEqual(
            get_appliance_type("IFB 7 kg 5 Star Front Load Fully Automatic Washing Machine"),
            "🫧 Washing Machines",
        )
        self.assertEqual(
            get_appliance_type("LG 8 kg Semi-Automatic Top Load Washer"),
            "🫧 Washing Machines",
        )

    def test_microwave_classification(self):
        self.assertEqual(
            get_appliance_type("IFB 30 L Convection Microwave Oven"),
            "📡 Microwaves & Ovens",
        )

    def test_television_classification(self):
        self.assertEqual(
            get_appliance_type("Sony Bravia 55 inch 4K Ultra HD Smart LED TV"),
            "📺 Televisions (TV)",
        )

    def test_department_classification(self):
        self.assertEqual(get_department_name("home_appliances"), "🧺 HOME APPLIANCES")
        self.assertEqual(get_department_name("mobiles"), "💻📱 GADGETS & CONSUMER ELECTRONICS")
        self.assertEqual(get_department_name("laptops"), "💻📱 GADGETS & CONSUMER ELECTRONICS")


class TestGenericSpecExtraction(unittest.TestCase):
    def test_appliance_specs(self):
        title = "Bosch 8 kg 1400 RPM 5 Star Inverter Front Load Washing Machine"
        specs = extract_generic_specs(title)
        self.assertEqual(specs.get("Capacity"), "8 kg")
        self.assertEqual(specs.get("Speed"), "1400 RPM")
        self.assertEqual(specs.get("Energy"), "5★ Star")
        self.assertEqual(specs.get("Type"), "Front Load")
        self.assertEqual(specs.get("Tech"), "Inverter")

    def test_laptop_specs(self):
        title = "Apple MacBook Air Apple M3 16 GB 512 GB SSD macOS"
        specs = extract_generic_specs(title)
        self.assertEqual(specs.get("RAM"), "16 GB")
        self.assertEqual(specs.get("Storage"), "512 GB")
        self.assertEqual(specs.get("Processor"), "M3")


if __name__ == "__main__":
    unittest.main()
