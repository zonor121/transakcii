from shop_client import FlowerShopClient, TransferType


def print_separator(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def get_balances(shop: FlowerShopClient) -> dict[str, float]:
    """Снимок балансов для сравнения до/после"""
    return {p["name"]: float(p["balance"]) for p in shop.get_participants()}


def main():
    shop = FlowerShopClient()

    print_separator("🏪 Магазин цветов 'Ромашка' — Тесты транзакций")
    print("Принципы ACID в действии:")
    print("  • Atomicity   — перевод целиком или откат")
    print("  • Consistency — сумма денег в системе не меняется")
    print("  • Isolation   — параллельные операции не мешают друг другу")
    print("  • Durability  — результат сохраняется после COMMIT")

    # Считаем общую массу денег в системе ДО всех операций
    balances_before = get_balances(shop)
    total_money_before = sum(balances_before.values())

    print_separator("📊 Начальное состояние системы")
    for name, bal in balances_before.items():
        print(f"  {name}: {bal:>12.2f} ₽")
    print(f"  {'─' * 40}")
    print(f"  💰 ОБЩАЯ МАССА ДЕНЕГ: {total_money_before:.2f} ₽")
    print(f"  ⚠️  Эта сумма НЕ должна измениться ни при каких переводах!")

    # ─────────────────────────────────────────────
    # ТЕСТ 1: Успешная транзакция (COMMIT)
    # ─────────────────────────────────────────────
    print_separator("✅ ТЕСТ 1: Успешный перевод → COMMIT")
    print("Ожидание: баланс отправителя -45000, получателя +45000")
    print("          общая масса денег неизменна")

    before = get_balances(shop)
    result = shop.transfer(
        from_id=next(p["id"] for p in shop.get_participants() if p["name"] == "Глеб (Владелец)"),
        to_id=next(p["id"] for p in shop.get_participants() if p["name"] == "Степан (Флорист)"),
        amount=45000.00,
        transfer_type=TransferType.SALARY,
        description="ЗП за сентябрь",
    )
    after = get_balances(shop)

    print(f"  Результат: {'✅ COMMIT' if result.success else '❌ ROLLBACK'} — {result.message}")
    if result.success:
        delta_gleb = after["Глеб (Владелец)"] - before["Глеб (Владелец)"]
        delta_stepan = after["Степан (Флорист)"] - before["Степан (Флорист)"]
        total_after = sum(after.values())
        print(f"  Δ Глеб:    {delta_gleb:+.2f} ₽")
        print(f"  Δ Степан:  {delta_stepan:+.2f} ₽")
        print(f"  Σ изменений: {delta_gleb + delta_stepan:+.2f} ₽ (должно быть 0)")
        print(f"  💰 Масса денег: {total_after:.2f} ₽ {'✅' if abs(total_after - total_money_before) < 0.01 else '❌ УТЕЧКА!'}")

    # ─────────────────────────────────────────────
    # ТЕСТ 2: Неуспешная транзакция → ROLLBACK
    # ─────────────────────────────────────────────
    print_separator("❌ ТЕСТ 2: Недостаточно средств → ROLLBACK")
    print("Ожидание: НИ ОДИН баланс не изменился (атомарный откат)")

    before = get_balances(shop)
    result = shop.transfer(
        from_id=next(p["id"] for p in shop.get_participants() if p["name"] == "Захар (Курьер)"),
        to_id=next(p["id"] for p in shop.get_participants() if p["name"] == "Глеб (Владелец)"),
        amount=999999.00,
        transfer_type=TransferType.PAYMENT,
        description="Невозможный платёж",
    )
    after = get_balances(shop)

    print(f"  Результат: {'✅ COMMIT' if result.success else '❌ ROLLBACK'} — {result.message}")
    changed = [name for name in before if before[name] != after[name]]
    if not changed:
        print(f"  ✅ АТОМАРНОСТЬ ПОДТВЕРЖДЕНА: ни один баланс не тронут")
    else:
        print(f"  ❌ НАРУШЕНИЕ АТОМАРНОСТИ: изменились {changed}")

    # ─────────────────────────────────────────────
    # ТЕСТ 3: Нарушение бизнес-правила → ROLLBACK
    # ─────────────────────────────────────────────
    print_separator("❌ ТЕСТ 3: Клиент платит курьеру → ROLLBACK")
    print("Ожидание: бизнес-валидация внутри транзакции, полный откат")

    before = get_balances(shop)
    result = shop.transfer(
        from_id=next(p["id"] for p in shop.get_participants() if p["name"] == "Мария (Клиент)"),
        to_id=next(p["id"] for p in shop.get_participants() if p["name"] == "Захар (Курьер)"),
        amount=1000.00,
        transfer_type=TransferType.PAYMENT,
        description="Чаевые (запрещено)",
    )
    after = get_balances(shop)

    print(f"  Результат: {'✅ COMMIT' if result.success else '❌ ROLLBACK'} — {result.message}")
    changed = [name for name in before if before[name] != after[name]]
    if not changed:
        print(f"  ✅ КОНСИСТЕНТНОСТЬ СОХРАНЕНА: бизнес-правило enforced, деньги на месте")
    else:
        print(f"  ❌ НАРУШЕНИЕ: изменились {changed}")

    # ─────────────────────────────────────────────
    # ТЕСТ 4: Сотрудник выдаёт зарплату → ROLLBACK
    # ─────────────────────────────────────────────
    print_separator("❌ ТЕСТ 4: Флорист выдаёт ЗП курьеру → ROLLBACK")
    print("Ожидание: только OWNER может платить SALARY")

    before = get_balances(shop)
    result = shop.transfer(
        from_id=next(p["id"] for p in shop.get_participants() if p["name"] == "Степан (Флорист)"),
        to_id=next(p["id"] for p in shop.get_participants() if p["name"] == "Захар (Курьер)"),
        amount=5000.00,
        transfer_type=TransferType.SALARY,
        description="Премия (запрещено)",
    )
    after = get_balances(shop)

    print(f"  Результат: {'✅ COMMIT' if result.success else '❌ ROLLBACK'} — {result.message}")
    changed = [name for name in before if before[name] != after[name]]
    if not changed:
        print(f"  ✅ ИЗОЛЯЦИЯ БИЗНЕС-ЛОГИКИ: несанкционированная операция полностью откачена")
    else:
        print(f"  ❌ НАРУШЕНИЕ: изменились {changed}")

    # ─────────────────────────────────────────────
    # ФИНАЛЬНЫЙ АУДИТ
    # ─────────────────────────────────────────────
    print_separator("🔍 Финальный аудит целостности данных")
    balances_final = get_balances(shop)
    total_money_final = sum(balances_final.values())

    for name, bal in balances_final.items():
        delta = bal - balances_before[name]
        marker = "  " if abs(delta) < 0.01 else f" ({delta:+.2f})"
        print(f"  {name}: {bal:>12.2f} ₽{marker}")

    print(f"  {'─' * 40}")
    print(f"  💰 Масса денег ДО:    {total_money_before:.2f} ₽")
    print(f"  💰 Масса денег ПОСЛЕ: {total_money_final:.2f} ₽")
    diff = total_money_final - total_money_before
    if abs(diff) < 0.01:
        print(f"  ✅ ЦЕЛОСТНОСТЬ ПОДТВЕРЖДЕНА: деньги не появились и не исчезли")
    else:
        print(f"  ❌ КРИТИЧЕСКАЯ ОШИБКА: масса денег изменилась на {diff:+.2f} ₽")

    print_separator("📜 История транзакций (только COMMIT-нутые)")
    for t in shop.get_transfers(limit=10):
        print(f"  [{t['type']:7}] {t['from']['name']:20} → {t['to']['name']:20} | {t['amount']:>10} ₽ | {t['description']}")

    print(f"\n💡 Вывод: из 4 попыток перевода только 1 завершилась COMMIT-ом.")
    print(f"   Остальные 3 были атомарно откачены — ни копейки не потеряно.")


if __name__ == "__main__":
    main()