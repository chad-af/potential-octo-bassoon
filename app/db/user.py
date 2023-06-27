from fireo.models import Model
from fireo.fields import TextField, IDField, DateTime


class DBUser(Model):
    id = IDField()
    user_id = TextField()
    shopify_customer_id = TextField()
    email = TextField()
    created_at = DateTime(auto=True)
    updated_at = DateTime(auto=True)
    last_login_at = DateTime(auto=True)

    class Meta:
        collection_name = "user"


def get_by_shopify_customer_id(shopify_customer_id: str) -> DBUser:
    user = DBUser.collection.filter(
        "shopify_customer_id", "==", shopify_customer_id
    ).get()
    return user


def get_by_email(email: str) -> DBUser:
    user = DBUser.collection.filter("email", "==", email).get()
    return user


def get_by_user_id(user_id: str) -> DBUser:
    user = DBUser.collection.filter("user_id", "==", user_id).get()
    return user
