from decimal import Decimal
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from orders.models import Cart, CartItem, Order, OrderItem
from posts.models import Post
from rest_framework.test import APIClient

User = get_user_model()

PASSWORD = "sup3rsecret!"  # pragma: allowlist secret
SHIPPING = {
    "shipping_name": "Alice",
    "shipping_address": "1 Test St",
    "shipping_city": "Dublin",
    "shipping_zip": "D01",
    "shipping_country": "IE",
}


# ======================================================================
# Fixtures
# ======================================================================

# === api client + users ===


@pytest.fixture
def api() -> APIClient:
    return APIClient(enforce_csrf_checks=False)


@pytest.fixture
def alice(db) -> Any:  # type: ignore[no-untyped-def]
    return User.objects.create_user(email="alice@example.com", password=PASSWORD)


@pytest.fixture
def bob(db) -> Any:  # type: ignore[no-untyped-def]
    return User.objects.create_user(email="bob@example.com", password=PASSWORD)


@pytest.fixture
def alice_api(api: APIClient, alice: Any) -> APIClient:
    resp = api.post(
        reverse("auth:login"),
        data={"email": alice.email, "password": PASSWORD},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    return api


@pytest.fixture
def bob_api(api: APIClient, bob: Any) -> APIClient:
    fresh = APIClient(enforce_csrf_checks=False)
    resp = fresh.post(
        reverse("auth:login"),
        data={"email": bob.email, "password": PASSWORD},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    return fresh


# === posts ===


@pytest.fixture
def mug(bob: Any) -> Post:
    return Post.objects.create(owner=bob, caption="Mug", price=Decimal("9.99"))


@pytest.fixture
def shirt(bob: Any) -> Post:
    return Post.objects.create(owner=bob, caption="Shirt", price=Decimal("19.99"))


@pytest.fixture
def freebie(bob: Any) -> Post:
    return Post.objects.create(owner=bob, caption="Free pic", price=None)


# ======================================================================
# Cart get + add
# ======================================================================


@pytest.mark.django_db
def test_cart_is_autocreated_on_first_get(alice_api: APIClient, alice: Any) -> None:
    resp = alice_api.get(reverse("cart:cart"))
    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert Decimal(resp.json()["total"]) == Decimal("0")
    assert Cart.objects.filter(user=alice).exists()


@pytest.mark.django_db
def test_cart_get_requires_auth(api: APIClient) -> None:
    resp = api.get(reverse("cart:cart"))
    assert resp.status_code == 401


@pytest.mark.django_db
def test_add_item_creates_row(alice_api: APIClient, mug: Post) -> None:
    resp = alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": mug.id, "qty": 2},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["qty"] == 2
    item = CartItem.objects.get(post=mug)
    assert item.qty == 2


@pytest.mark.django_db
def test_add_item_dedupes_same_post(alice_api: APIClient, mug: Post) -> None:
    alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": mug.id, "qty": 1},
        format="json",
    )
    resp = alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": mug.id, "qty": 3},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["qty"] == 4
    assert CartItem.objects.filter(post=mug).count() == 1


@pytest.mark.django_db
def test_add_item_rejects_priceless_post(alice_api: APIClient, freebie: Post) -> None:
    resp = alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": freebie.id, "qty": 1},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_add_item_rejects_missing_post(alice_api: APIClient) -> None:
    resp = alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": 99999, "qty": 1},
        format="json",
    )
    assert resp.status_code == 400


# ======================================================================
# Cart update + delete
# ======================================================================


@pytest.mark.django_db
def test_patch_item_sets_absolute_qty(alice_api: APIClient, mug: Post) -> None:
    add = alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": mug.id, "qty": 2},
        format="json",
    )
    item_id = add.json()["id"]
    resp = alice_api.patch(
        reverse("cart:cart-item-detail", args=[item_id]),
        data={"qty": 5},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["qty"] == 5


@pytest.mark.django_db
def test_patch_item_other_users_returns_404(
    alice_api: APIClient, bob_api: APIClient, mug: Post
) -> None:
    add = bob_api.post(
        reverse("cart:cart-items"),
        data={"post_id": mug.id, "qty": 1},
        format="json",
    )
    item_id = add.json()["id"]
    resp = alice_api.patch(
        reverse("cart:cart-item-detail", args=[item_id]),
        data={"qty": 9},
        format="json",
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_delete_item_removes_row(alice_api: APIClient, mug: Post) -> None:
    add = alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": mug.id, "qty": 1},
        format="json",
    )
    item_id = add.json()["id"]
    resp = alice_api.delete(reverse("cart:cart-item-detail", args=[item_id]))
    assert resp.status_code == 204
    assert not CartItem.objects.filter(pk=item_id).exists()


@pytest.mark.django_db
def test_cart_total_reflects_items(alice_api: APIClient, mug: Post, shirt: Post) -> None:
    alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": mug.id, "qty": 2},
        format="json",
    )
    alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": shirt.id, "qty": 1},
        format="json",
    )
    resp = alice_api.get(reverse("cart:cart"))
    assert Decimal(resp.json()["total"]) == Decimal("9.99") * 2 + Decimal("19.99")


# ======================================================================
# Checkout
# ======================================================================


@pytest.mark.django_db
def test_checkout_creates_order_and_clears_cart(
    alice_api: APIClient, alice: Any, mug: Post, shirt: Post
) -> None:
    alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": mug.id, "qty": 2},
        format="json",
    )
    alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": shirt.id, "qty": 1},
        format="json",
    )
    resp = alice_api.post(
        reverse("orders:checkout"),
        data={"payment_method": "card", **SHIPPING},
        format="json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "paid"
    assert Decimal(body["total"]) == Decimal("9.99") * 2 + Decimal("19.99")
    assert len(body["items"]) == 2
    order = Order.objects.get(pk=body["id"])
    assert order.user_id == alice.id
    assert order.payment_method == "card"
    assert order.shipping_city == "Dublin"
    assert OrderItem.objects.filter(order=order).count() == 2
    assert CartItem.objects.filter(cart__user=alice).count() == 0


@pytest.mark.django_db
def test_checkout_snapshots_price(alice_api: APIClient, mug: Post) -> None:
    alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": mug.id, "qty": 1},
        format="json",
    )
    alice_api.post(
        reverse("orders:checkout"),
        data={"payment_method": "card", **SHIPPING},
        format="json",
    )
    # owner bumps the price after sale; the order should still see the old one
    mug.price = Decimal("99.99")
    mug.save(update_fields=["price"])
    item = OrderItem.objects.get(post=mug)
    assert item.price_at_purchase == Decimal("9.99")


@pytest.mark.django_db
def test_checkout_empty_cart_returns_400(alice_api: APIClient) -> None:
    resp = alice_api.post(
        reverse("orders:checkout"),
        data={"payment_method": "card", **SHIPPING},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_checkout_unknown_payment_method_returns_400(alice_api: APIClient, mug: Post) -> None:
    alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": mug.id, "qty": 1},
        format="json",
    )
    resp = alice_api.post(
        reverse("orders:checkout"),
        data={"payment_method": "bitcoin-vouchers", **SHIPPING},
        format="json",
    )
    assert resp.status_code == 400


# ======================================================================
# Orders history
# ======================================================================


@pytest.mark.django_db
def test_orders_list_returns_only_my_orders(
    alice_api: APIClient, bob_api: APIClient, mug: Post
) -> None:
    for client in (alice_api, bob_api):
        client.post(
            reverse("cart:cart-items"),
            data={"post_id": mug.id, "qty": 1},
            format="json",
        )
        client.post(
            reverse("orders:checkout"),
            data={"payment_method": "card", **SHIPPING},
            format="json",
        )
    resp = alice_api.get(reverse("orders:order-list"))
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 1


@pytest.mark.django_db
def test_order_detail_404_for_other_user(
    alice_api: APIClient, bob_api: APIClient, mug: Post
) -> None:
    bob_api.post(
        reverse("cart:cart-items"),
        data={"post_id": mug.id, "qty": 1},
        format="json",
    )
    bob_checkout = bob_api.post(
        reverse("orders:checkout"),
        data={"payment_method": "card", **SHIPPING},
        format="json",
    )
    other_order_id = bob_checkout.json()["id"]
    resp = alice_api.get(reverse("orders:order-detail", args=[other_order_id]))
    assert resp.status_code == 404


@pytest.mark.django_db
def test_order_detail_owner_sees_full_payload(alice_api: APIClient, mug: Post) -> None:
    alice_api.post(
        reverse("cart:cart-items"),
        data={"post_id": mug.id, "qty": 1},
        format="json",
    )
    checkout = alice_api.post(
        reverse("orders:checkout"),
        data={"payment_method": "paypal", **SHIPPING},
        format="json",
    )
    order_id = checkout.json()["id"]
    resp = alice_api.get(reverse("orders:order-detail", args=[order_id]))
    assert resp.status_code == 200
    assert resp.json()["payment_method"] == "paypal"
    assert len(resp.json()["items"]) == 1
