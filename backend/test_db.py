from db import init_db, search_products, reduce_stock

init_db()

print("Black shoes under $50:")
print(search_products(category="shoes", color="black", max_price=50))

print("Size 8 shoes:")
print(search_products(category="shoes", size="8"))

reduce_stock(1)
print("After reduce_stock(1):")
print(search_products(category="shoes", color="black", max_price=50))