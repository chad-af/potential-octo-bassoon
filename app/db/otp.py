import random
import string
import pytz

from asyncio.log import logger
from datetime import datetime
from fireo.fields import IDField, TextField, DateTime, NumberField
from fireo.models import Model

MAX_TRY_COUNT = 3


class DBOtp(Model):
    id = IDField()
    email = TextField()
    code = TextField()
    try_count = NumberField(default=0, int_only=True)
    send_count = NumberField(default=0, int_only=True)
    created_at = DateTime(auto=True)
    updated_at = DateTime(auto=True)

    class Meta:
        collection_name = "otp"


def update(email: str, otp: DBOtp):
    otp.update(email)


def get_by_email(email: str) -> DBOtp:
    otp = DBOtp.collection.filter("email", "==", email).get()
    return otp


def get_random_otp(k=4) -> str:
    return "".join(random.choices(string.digits, k=k))


def verify(email, code) -> bool:

    try:
        otp = get_by_email(email)

        if otp.code == code:
            DBOtp.collection.delete(otp.key)
            return True

        if otp.try_count >= MAX_TRY_COUNT:
            DBOtp.collection.delete(otp.key)
            return False
        otp.try_count += 1
        otp.updated_at = datetime.now(pytz.timezone("UTC"))
        otp.update()
        return False
    except Exception as e:
        logger.error(e)
        return False
