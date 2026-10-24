import csv


def find_inconsistent_orders(path):
    issues = []
    with open(path, newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            quantity = int(row["quantity"])
            unit_price = float(row["unit_price"])
            amount = float(row["amount"])
            if amount != quantity * unit_price:
                issues.append(row["order_id"])
    return issues


# 固定合成示例：这里只展示代码，不会执行。
