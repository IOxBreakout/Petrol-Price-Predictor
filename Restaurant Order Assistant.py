import re
import difflib

# ---------- MENU ----------
menu = {
    "Pizza": {
        "Margherita": {"price": 1200, "veg": True},
        "Pepperoni": {"price": 1500, "veg": False},
        "BBQ Chicken": {"price": 1800, "veg": False},
        "Veggie Delight": {"price": 1300, "veg": True},
        "Cheese Lover": {"price": 2000, "veg": True},
    },
    "Calzones": {
        "Cheese Calzone": {"price": 1400, "veg": True},
        "Chicken Calzone": {"price": 1600, "veg": False},
    },
    "Drinks": {
        "Coke": {"price": 200, "veg": True},
        "Sprite": {"price": 200, "veg": True},
        "Sting": {"price": 250, "veg": True},
        "Water Bottle": {"price": 100, "veg": True},
    }
}

# ---------- HELPERS ----------
def normalize_text(text):
    return text.lower().strip()

def get_all_items():
    return {item: details["price"] for cat in menu.values() for item, details in cat.items()}

def fuzzy_match(query):
    items = get_all_items().keys()
    match = difflib.get_close_matches(query, items, n=1, cutoff=0.6)
    return match[0] if match else None

def parse_shorthand_price(price_str):
    """Parses '2k' → 2000, '1.5k' → 1500, '200' → 200"""
    price_str = price_str.lower().replace(",", "")
    if "k" in price_str:
        return int(float(price_str.replace("k", "")) * 1000)
    return int(float(price_str))

def format_results(results, title="Results"):
    if not results:
        return f"❌ No {title.lower()} found."
    out = [f"\n📋 {title}:"]
    for item, price in results.items():
        out.append(f" - {item}: {price}/-")
    return "\n".join(out)

def show_menu():
    print("\n📖 Full Menu:")
    for category, items in menu.items():
        emoji = "🍕" if category == "Pizza" else "🥟" if category == "Calzones" else "🥤"
        print(f"\n{emoji} {category}")
        for item, details in items.items():
            veg_icon = "🌱" if details.get("veg") else "🍖"
            print(f"   {veg_icon} {item} - {details['price']}/-")

# ---------- ORDER SYSTEM ----------
cart = []
reservations = []

def add_to_cart(item_name):
    all_items = get_all_items()
    match = difflib.get_close_matches(item_name, all_items.keys(), n=1, cutoff=0.6)
    if match:
        cart.append(match[0])
        return f"🛒 Added {match[0]} ({all_items[match[0]]}/-) to your cart."
    return f"❌ '{item_name}' not found in menu."

def undo_last_add():
    if not cart:
        return "⚠️ Cart is empty."
    removed = cart.pop()
    return f"↩️ Removed {removed} from cart."

def view_cart():
    if not cart:
        return "🛒 Your cart is empty."
    items = {}
    total = 0
    for item in cart:
        price = get_all_items()[item]
        total += price
        items[item] = items.get(item, 0) + 1
    out = ["\n🛒 Your Cart:"]
    for item, qty in items.items():
        out.append(f" - {item} x{qty} = {qty * get_all_items()[item]}/-")
    out.append(f"\n💰 Total: {total}/-")
    return "\n".join(out)

def checkout():
    if not cart:
        return "⚠️ Your cart is empty."
    total = sum(get_all_items()[item] for item in cart)
    cart.clear()
    return f"✅ Order placed successfully! Total bill: {total}/-"

# ---------- RESERVATIONS ----------
def make_reservation(name, people, time):
    reservations.append({"name": name, "people": people, "time": time})
    return f"📅 Reservation confirmed for {people} people at {time}. (Name: {name})"

def view_reservations():
    if not reservations:
        return "📭 No reservations yet."
    out = ["\n📅 Reservations:"]
    for r in reservations:
        out.append(f" - {r['name']}, {r['people']} people at {r['time']}")
    return "\n".join(out)

# ---------- MAIN QUERY HANDLER ----------
def check_availability(query):
    query = normalize_text(query)

    # --- Detect category ---
    category_filter = None
    for category in menu.keys():
        if category.lower() in query:
            category_filter = category
            break

    def filtered_items():
        if category_filter:
            return {i: d["price"] for i, d in menu[category_filter].items()}
        return get_all_items()

    # --- Handle price queries ---
    range_match = re.search(r'(\d+(\.\d+)?k?)(?:\s*[-to]+\s*)(\d+(\.\d+)?k?)', query)
    under_match = re.search(r'under (\d+(\.\d+)?k?)', query)
    above_match = re.search(r'(above|over|greater than|more than) (\d+(\.\d+)?k?)', query)
    cheaper_match = re.search(r'(cheaper|less than) (\d+(\.\d+)?k?)', query)
    expensive_match = re.search(r'(costing|priced) (more|above) (\d+(\.\d+)?k?)', query)

    items = filtered_items()

    if range_match:
        low = parse_shorthand_price(range_match.group(1))
        high = parse_shorthand_price(range_match.group(3))
        results = {i: p for i, p in items.items() if low <= p <= high}
        return format_results(results, f"{category_filter or 'Items'} priced between {low} and {high}")
    elif under_match or cheaper_match:
        price_str = under_match.group(1) if under_match else cheaper_match.group(2)
        price = parse_shorthand_price(price_str)
        results = {i: p for i, p in items.items() if p <= price}
        return format_results(results, f"{category_filter or 'Items'} under {price}")
    elif above_match:
        price = parse_shorthand_price(above_match.group(2))
        results = {i: p for i, p in items.items() if p >= price}
        return format_results(results, f"{category_filter or 'Items'} above {price}")
    elif expensive_match:
        price = parse_shorthand_price(expensive_match.group(3))
        results = {i: p for i, p in items.items() if p >= price}
        return format_results(results, f"{category_filter or 'Items'} above {price}")

    # --- Cheapest / Expensive ---
    if "cheapest" in query or "lowest price" in query:
        item = min(items, key=items.get)
        return f"💰 Cheapest {category_filter or 'item'}: {item} ({items[item]}/-)"
    if "expensive" in query or "costliest" in query:
        item = max(items, key=items.get)
        return f"💎 Most expensive {category_filter or 'item'}: {item} ({items[item]}/-)"

    # --- Category listing ---
    if category_filter:
        return format_results(items, f"Available {category_filter}")

    # --- Specific item check ---
    for cat, its in menu.items():
        for item in its:
            if item.lower() in query:
                return f"✅ Yes, we have {item} for {its[item]['price']}/-"

    # --- Fuzzy match ---
    possible_item = fuzzy_match(query)
    if possible_item:
        for cat, its in menu.items():
            if possible_item in its:
                return f"✅ Did you mean '{possible_item}'? It's available for {its[possible_item]['price']}/-"

    return f"❌ Sorry, '{query}' is not on the menu."

# ---------- CLI ----------
def cli():
    print("🍽️ Welcome to the Restaurant Order Assistant!")
    print("👉 Ask me about any item")
    print("👉 Type 'menu' to see full menu, 'add <item>' to order, 'undo' to remove last added item, 'cart' to view cart, 'checkout' to place order, 'reserve' to book a table, 'help' for commands, or 'exit' to quit.")

    while True:
        user_input = input("\n> ").strip()
        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("👋 Goodbye! Thanks for visiting.")
            break
        elif user_input.lower() == "menu":
            show_menu()
        elif user_input.lower().startswith("add "):
            item = user_input[4:].strip()
            print(add_to_cart(item))
        elif user_input.lower() == "undo":
            print(undo_last_add())
        elif user_input.lower() == "cart":
            print(view_cart())
        elif user_input.lower() == "checkout":
            print(checkout())
        elif user_input.lower() == "reserve":
            name = input("Your name: ")
            people = input("Number of people: ")
            time = input("Reservation time: ")
            print(make_reservation(name, people, time))
        elif user_input.lower() == "reservations":
            print(view_reservations())
        elif user_input.lower() == "help":
            print("\n📖 Commands:")
            print(" - menu → Show menu")
            print(" - add <item> → Add item to cart")
            print(" - undo → Remove last added item")
            print(" - cart → View cart")
            print(" - checkout → Confirm order and clear cart")
            print(" - reserve → Make a reservation")
            print(" - reservations → View all reservations")
            print(" - exit → Quit")
            print(" - Or just ask about items/prices (e.g., 'Do you have pizza?', 'Any veg drinks under 200?')")
        else:
            print(check_availability(user_input))


# ---------- R
