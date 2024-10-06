from decimal import Decimal


class Quotation():

    units: int
    nano: int

    def __init__(self, inQuotation=None, units=0, nano=0):
        if inQuotation is None:
            self.units = units
            self.nano = nano
            return
        self.units = inQuotation.units
        self.nano = inQuotation.nano

    def to_integer(self):
        return self.units

    def to_decimal(self) -> Decimal:
        value = f"{self.units}."
        if self.units < 0:
            self.nano = abs(self.nano)
        elif self.units == 0 and self.nano < 0:
            value = "-" + value
            self.nano = abs(self.nano)
        value += self.nano.__str__().zfill(9)
        return Decimal(value)
