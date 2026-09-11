from shop_client import FlowerShopClient, TransferType


def main():
    shop = FlowerShopClient()

    # Получаем ID участников
    participants = shop.get_participants()
    ids = {p["name"]: p["id"] for p in participants}

    print("=== Начальные балансы ===")
    for p in participants:
        print(f"  {p['name']} ({p['role']}): {p['balance']} ₽")

    # ✅ Зарплата флористу Степану
    print("\n--- Зарплата Степану ---")
    result = shop.transfer(
        from_id=ids["Глеб (Владелец)"],
        to_id=ids["Степан (Флорист)"],
        amount=45000.00,
        transfer_type=TransferType.SALARY,
        description="ЗП за сентябрь",
    )
    print(f"  {'✅' if result.success else '❌'} {result.message}")
    if result.success:
        print(f"  Баланс Глеба: {result.sender_balance}, Степана: {result.receiver_balance}")

    # ✅ Оплата от клиента Марии
    print("\n--- Оплата от Марии ---")
    result = shop.transfer(
        from_id=ids["Мария (Клиент)"],
        to_id=ids["Глеб (Владелец)"],
        amount=3500.00,
        transfer_type=TransferType.PAYMENT,
        description='Букет "Нежность"',
    )
    print(f"  {'✅' if result.success else '❌'} {result.message}")

    # ❌ Клиент платит курьеру Захару (должно упасть)
    print("\n--- Чаевые Захару (ожидается отказ) ---")
    result = shop.transfer(
        from_id=ids["Мария (Клиент)"],
        to_id=ids["Захар (Курьер)"],
        amount=1000.00,
        transfer_type=TransferType.PAYMENT,
        description="Чаевые",
    )
    print(f"  {'✅' if result.success else '❌'} {result.message}")

    # ❌ Сотрудник выдаёт зарплату (должно упасть)
    print("\n--- Степан выдаёт ЗП Захару (ожидается отказ) ---")
    result = shop.transfer(
        from_id=ids["Степан (Флорист)"],
        to_id=ids["Захар (Курьер)"],
        amount=5000.00,
        transfer_type=TransferType.SALARY,
        description="Премия",
    )
    print(f"  {'✅' if result.success else '❌'} {result.message}")

    # Итоговые балансы
    print("\n=== Итоговые балансы ===")
    for p in shop.get_participants():
        print(f"  {p['name']} ({p['role']}): {p['balance']} ₽")

    # История переводов
    print("\n=== История переводов ===")
    for t in shop.get_transfers(limit=10):
        print(f"  [{t['type']}] {t['from']['name']} → {t['to']['name']}: {t['amount']} ₽ | {t['description']}")


if __name__ == "__main__":
    main()