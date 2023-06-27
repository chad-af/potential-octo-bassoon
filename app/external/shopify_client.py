import json

import shopify
from fastapi import Depends

from app.external.shopify.responses import ShopifyGetCustomerByOrderIdResponse
from app.secret_loader import init_setting
from app.secrets import Secrets


class ShopifyClient:
    def __init__(self, settings: Secrets = Depends(init_setting)):
        self.api_version = "2022-07"
        self.shopify_private_app_admin_api_access_token = (
            settings.shopify_private_app_admin_api_access_token
        )

    def initiate_session(self, shop_url: str):
        return shopify.Session(
            shop_url, self.api_version, self.shopify_private_app_admin_api_access_token
        )

    def initiate_temporary_session(self, shop_url: str):
        return shopify.Session.temp(
            shop_url, self.api_version, self.shopify_private_app_admin_api_access_token
        )

    def get_products(self, shop_url: str):
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """{
                products(first:10) {
                    edges {
                        node {
                            id
                            title
                        }
                    }
                }
            }"""
            )
            return json.loads(data)

    def get_coupon_by_title(self, shop_url: str, coupon_title):
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                '''{
                codeDiscountNodeByCode(code: "'''
                + coupon_title
                + """") {
                    id,
                    codeDiscount {
                        __typename
                        ... on DiscountCodeApp {
                            status
                            title
                        }
                        ... on DiscountCodeBasic {
                            status
                            title
                        }
                        ... on DiscountCodeBxgy {
                            status
                            title
                        }
                        ... on DiscountCodeFreeShipping {
                            status
                            title
                        }
                    }
                }
            }"""
            )
            return json.loads(data)

    def get_customer_by_order_id(
        self, shop_url: str, order_id: str
    ) -> ShopifyGetCustomerByOrderIdResponse:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            json_str = shopify.GraphQL().execute(
                f"""{{
                    order(id: "gid://shopify/Order/{order_id}") {{
                        customer {{
                            id
                            firstName
                            lastName
                            displayName
                            email
                            phone
                        }}
                    }}
                }}"""
            )
            json_dict = json.loads(json_str)
            return ShopifyGetCustomerByOrderIdResponse(**json_dict)

    def get_order_by_id(
        self, shop_url: str, order_id: str, get_refunded_items: bool = False
    ):
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """{
                order(id: "gid://shopify/Order/"""
                + order_id
                + """") {
                    id
                    name
                    createdAt
                    updatedAt
                    processedAt
                    displayFinancialStatus
                    displayFulfillmentStatus
                    location
                    currencyCode
                    customer {
                        id
                        firstName
                        lastName
                        displayName
                        email
                        phone
                    }
                    shippingAddress {
                        id
                        address1
                        address2
                        city
                        company
                        country
                        countryCodeV2
                        name
                        firstName
                        lastName
                        phone
                        province
                        provinceCode
                        zip
                        latitude
                        longitude
                        coordinatesValidated
                    }
                    fulfillments {
                        id
                        name
                        createdAt
                        updatedAt
                        deliveredAt
                        status
                        displayStatus
                        estimatedDeliveryAt
                        requiresShipping
                        trackingInfo {
                            number
                            company
                            url
                        }
                    }
                    totalShippingPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    totalTaxSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    currentTotalTaxSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    totalPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    currentTotalPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    subtotalPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    currentSubtotalPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    totalDiscountsSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    currentTotalDiscountsSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    totalOutstandingSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    transactions {
                        gateway
                        id
                        kind
                        amountSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }
                    }
                    refunds(first: 10) {
                        id
                        totalRefundedSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }
                    }
                    lineItems(first:10) {
                        edges {
                            node {
                                id
                                name
                                image {
                                    url
                                }
                                variant {
                                    id
                                    title
                                    displayName
                                    selectedOptions {
                                        name
                                        value
                                    }
                                }
                                product {
                                    id
                                    totalVariants
                                }
                                quantity
                                currentQuantity
                                refundableQuantity
                                originalUnitPriceSet {
                                    shopMoney {
                                        amount
                                        currencyCode
                                    }
                                }
                                discountedUnitPriceSet {
                                    shopMoney {
                                        amount
                                        currencyCode
                                    }
                                }
                                discountedTotalSet {
                                    shopMoney {
                                        amount
                                        currencyCode
                                    }
                                }
                                discountAllocations {
                                    allocatedAmountSet {
                                        shopMoney {
                                            amount
                                            currencyCode
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }"""
            )

            result = json.loads(data)
            order_details = result.get("data", {}).get("order", {})
            line_items = []
            for edge in order_details.get("lineItems", {}).get("edges", []):
                node = edge.get("node", {})
                if get_refunded_items:
                    edge["node"]["currentQuantity"] = node.get("quantity", 0)
                    line_items.append(edge)
                else:
                    current_quantity = node.get("currentQuantity", 0)
                    refundable_quantity = node.get("refundableQuantity", 0)
                    if current_quantity == refundable_quantity == 0:
                        continue
                    line_items.append(edge)

            if get_refunded_items:
                result["data"]["order"]["currentSubtotalPriceSet"] = result["data"][
                    "order"
                ]["subtotalPriceSet"]
                result["data"]["order"]["currentTotalDiscountsSet"] = result["data"][
                    "order"
                ]["totalDiscountsSet"]
                result["data"]["order"]["currentTotalPriceSet"] = result["data"][
                    "order"
                ]["totalPriceSet"]
                result["data"]["order"]["currentTotalTaxSet"] = result["data"]["order"][
                    "totalTaxSet"
                ]

            result["data"]["order"]["lineItems"]["edges"] = line_items
            return result

    def get_order_by_number(self, shop_url: str, order_name):
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """{
                orders(first:10, query: "name:"""
                + order_name
                + """") {
                    edges {
                        node {
                            id
                            name
                            createdAt
                            email
                            fulfillments {
                                id
                                displayStatus
                            }
                            customer {
                                id
                                email
                           }
                        }
                    }
                    pageInfo {
                        startCursor
                        endCursor
                        hasNextPage
                        hasPreviousPage
                    }
                }
            }"""
            )
            return json.loads(data)

    def get_order_by_email(self, shop_url: str, email: str) -> json:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """{
                orders(first:10, query: "email:"""
                + email
                + """", sortKey:CREATED_AT, reverse:true) {
                    edges {
                        node {
                            id
                            name
                            createdAt
                            displayFinancialStatus
                            displayFulfillmentStatus
                            fulfillments {
                                id
                                name
                                createdAt
                                deliveredAt
                                displayStatus
                                estimatedDeliveryAt
                            }
                            totalPriceSet {
                                shopMoney {
                                    amount
                                    currencyCode
                                }
                            }
                            currentTotalPriceSet {
                                shopMoney {
                                    amount
                                    currencyCode
                                }
                            }
                            lineItems(first:10) {
                                edges {
                                    node {
                                        id
                                        name
                                        image {
                                            url
                                        }
                                    }
                                }
                            }
                        }
                    }
                    pageInfo {
                        startCursor
                        endCursor
                        hasNextPage
                        hasPreviousPage
                    }
                },
                customers(first:1, query: "email:"""
                + email
                + """") {
                    edges {
                        node {
                            id
                            firstName
                            lastName
                        }
                    }
                    pageInfo {
                        startCursor
                        endCursor
                        hasNextPage
                        hasPreviousPage
                    }
                }
            }"""
            )
            return json.loads(data)

    def get_orders_by_customer_id(self, shop_url: str, customer_id: str) -> json:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                '''{
                customer(id: "'''
                + customer_id
                + """") {
                    orders(first:10, sortKey:CREATED_AT, reverse:true) {
                        edges {
                            node {
                                id
                                name
                                createdAt
                                displayFinancialStatus
                                displayFulfillmentStatus
                                fulfillments {
                                    id
                                    name
                                    createdAt
                                    updatedAt
                                    deliveredAt
                                    status
                                    displayStatus
                                    estimatedDeliveryAt
                                    requiresShipping
                                    trackingInfo {
                                        number
                                        company
                                        url
                                    }
                                }
                                totalPriceSet {
                                    shopMoney {
                                        amount
                                        currencyCode
                                    }
                                }
                                currentTotalPriceSet {
                                    shopMoney {
                                        amount
                                        currencyCode
                                    }
                                }
                                totalOutstandingSet {
                                    shopMoney {
                                        amount
                                        currencyCode
                                    }
                                }
                                refunds(first: 10) {
                                    id
                                    totalRefundedSet {
                                        shopMoney {
                                            amount
                                            currencyCode
                                        }
                                    }
                                }
                                lineItems(first:10) {
                                    edges {
                                        node {
                                            id
                                            name
                                            image {
                                                url
                                            }
                                            currentQuantity
                                            refundableQuantity
                                        }
                                    }
                                }
                            }
                        }
                        pageInfo {
                            startCursor
                            endCursor
                            hasNextPage
                            hasPreviousPage
                        }
                    }
                }
            }"""
            )

            return json.loads(data)

    def get_customer_by_email(self, shop_url: str, email: str) -> json:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """{
                customers(first:1, query: "email:"""
                + email
                + """") {
                    edges {
                        node {
                            id
                            firstName
                            lastName
                        }
                    }
                    pageInfo {
                        startCursor
                        endCursor
                        hasNextPage
                        hasPreviousPage
                    }
                }
            }"""
            )
            return json.loads(data)

    def change_shipping_address(
        self,
        shop_url: str,
        order_id,
        first_name,
        last_name,
        address1,
        address2,
        city,
        province,
        country,
        zip_code,
    ) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """mutation {
                    orderUpdate(input: {
                        id: "gid://shopify/Order/"""
                + order_id
                + '''"
                        shippingAddress: {
                            firstName: "'''
                + first_name
                + '''"
                            lastName: "'''
                + last_name
                + '''"
                            address1: "'''
                + address1
                + '''"
                            address2: "'''
                + address2
                + '''"
                            city: "'''
                + city
                + '''"
                            province: "'''
                + province
                + '''"
                            country: "'''
                + country
                + '''"
                            zip: "'''
                + zip_code
                + """"
                        }
                    }) {
                        order {
                            id
                        }
                        userErrors {
                            field
                            message
                        }
                    }
                }"""
            )
            return json.loads(data)

    def refund_order(self, shop_url: str, order_id, refund_line_items, shipping_amount):
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """mutation {
                    refundCreate(
                        input: {
                            orderId: "gid://shopify/Order/"""
                + order_id
                + """"
                            notify: true
                            note: "Customer canceled order before it was shipped"
                            shipping: {
                                amount: """
                + str(shipping_amount)
                + """
                                fullRefund: true
                            }
                            refundLineItems: [
                            """
                + refund_line_items
                + """
                            ]
                        }
                    )
                    {

    refund {
      id
      order {
        currencyCode
        totalTaxSet {
          shopMoney {
            amount
            currencyCode
          }
        }
        updatedAt
        createdAt
        processedAt
        totalRefundedSet {
          shopMoney {
            amount
            currencyCode
          }
        }
        totalPriceSet {
            shopMoney {
                amount
                currencyCode
            }
        }
        subtotalPriceSet {
          shopMoney {
            amount
            currencyCode
          }
        }
      }
      totalRefundedSet {
        shopMoney {
          amount
          currencyCode
        }
      }
      refundLineItems(first: 100) {
        edges {
          node {
            lineItem {
              id
              name
              image {
                url
              }
              quantity
              currentQuantity
              totalDiscountSet {
                shopMoney {
                  amount
                  currencyCode
                }
              }
              discountedTotalSet {
                shopMoney {
                  amount
                  currencyCode
                }
              }
              originalUnitPriceSet {
                shopMoney {
                  amount
                  currencyCode
                }
              }
            }

          }
        }
      }
    }
                        userErrors {
                            field
                            message
                        }
                    }
                }"""
            )
            return json.loads(data)

    def get_fulfillment_orders_by_id(self, shop_url: str, order_id):
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """{
                order(id: "gid://shopify/Order/"""
                + order_id
                + """") {
                    id
                    name
                    createdAt
                    updatedAt
                    processedAt
                    displayFinancialStatus
                    displayFulfillmentStatus
                    location
                    currencyCode
                    customer {
                        id
                        firstName
                        lastName
                        displayName
                        email
                        phone
                    }
                    shippingAddress {
                        id
                        address1
                        address2
                        city
                        company
                        country
                        countryCodeV2
                        name
                        firstName
                        lastName
                        phone
                        province
                        provinceCode
                        zip
                        latitude
                        longitude
                        coordinatesValidated
                    }
                    fulfillments {
                        id
                        name
                        createdAt
                        updatedAt
                        deliveredAt
                        status
                        displayStatus
                        estimatedDeliveryAt
                        trackingInfo {
                            number
                            company
                            url
                        }
                    }
                    totalShippingPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    totalTaxSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    currentTotalTaxSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    totalPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    currentTotalPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    subtotalPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    currentSubtotalPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    totalDiscountsSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    currentTotalDiscountsSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    totalOutstandingSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    transactions {
                        gateway
                        id
                        kind
                        amountSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }
                    }
                    refunds(first: 10) {
                        id
                        totalRefundedSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }
                    }
                    lineItems(first:10) {
                        edges {
                            node {
                                id
                                name
                                image {
                                    url
                                }
                                variant {
                                    id
                                    title
                                    displayName
                                    selectedOptions {
                                        name
                                        value
                                    }
                                }
                                product {
                                    id
                                    totalVariants
                                }
                                currentQuantity
                                refundableQuantity
                                originalUnitPriceSet {
                                    shopMoney {
                                        amount
                                        currencyCode
                                    }
                                }
                                discountedUnitPriceSet {
                                    shopMoney {
                                        amount
                                        currencyCode
                                    }
                                }
                                discountedTotalSet {
                                    shopMoney {
                                        amount
                                        currencyCode
                                    }
                                }
                                discountAllocations {
                                    allocatedAmountSet {
                                        shopMoney {
                                            amount
                                            currencyCode
                                        }
                                    }
                                }
                            }
                        }
                    }
                    fulfillmentOrders(first: 10) {
                        edges {
                            node {
                                id
                                lineItems(first: 10) {
                                    edges {
                                        node {
                                            lineItem {
                                                id
                                                title
                                                quantity
                                                currentQuantity
                                                refundableQuantity
                                                discountedUnitPriceSet {
                                                    shopMoney {
                                                        amount
                                                        currencyCode
                                                    }
                                                }
                                                fulfillmentService {
                                                    id
                                                    location {
                                                        id
                                                        name
                                                    }
                                                    serviceName
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }"""
            )

            result = json.loads(data)
            order_details = result.get("data", {}).get("order", {})
            line_items = []
            for edge in (
                order_details.get("fulfillmentOrders", {})
                .get("edges", [])[0]
                .get("node", {})
                .get("lineItems", {})
                .get("edges", [])
            ):
                node = edge.get("node", {}).get("lineItem", {})
                current_quantity = node.get("currentQuantity", 0)
                refundable_quantity = node.get("refundableQuantity", 0)
                if current_quantity == refundable_quantity == 0:
                    continue
                line_items.append(edge)

            result["data"]["order"]["fulfillmentOrders"]["edges"][0]["node"][
                "lineItems"
            ]["edges"] = line_items

            line_items = []
            for edge in order_details.get("lineItems", {}).get("edges", []):
                node = edge.get("node", {})
                current_quantity = node.get("currentQuantity", 0)
                refundable_quantity = node.get("refundableQuantity", 0)
                if current_quantity == refundable_quantity == 0:
                    continue
                line_items.append(edge)

            result["data"]["order"]["lineItems"]["edges"] = line_items
            return result

    def get_line_item_info_by_id(self, shop_url: str, item_id: str) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """
                query {
                    node(id: "gid://shopify/LineItem/"""
                + item_id
                + """") {
                    ... on LineItem {
                        id
                        name
                        discountedUnitPriceSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }
                        quantity
                        discountAllocations {
                            allocatedAmountSet {
                                shopMoney {
                                    amount
                                    currencyCode
                                }
                            }
                            discountApplication {
                                allocationMethod
                            }
                        }
                        taxLines {
                            title
                            priceSet {
                                shopMoney {
                                    amount
                                    currencyCode
                                }
                            }
                        }
                        sku
                        image {
                            url
                        }
                    }
                }
                }
                """
            )
            return json.loads(data)

    def get_product_info_for_line_item(self, shop_url: str, item_id: str) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """
                query {
                    node(id: "gid://shopify/LineItem/"""
                + item_id
                + """") {
                           ... on LineItem {
                               id
      name
      product {
        id
        variants(first: 100) {
          edges {
            node {
              id
              price
              availableForSale
              inventoryQuantity
              displayName
              selectedOptions {
                name
                value
              }
              image {
                url
                id
              }
            }
          }
        }
      }
                           }
                       }
                       }
                       """
            )
            return json.loads(data)

    def get_variants_for_product(self, shop_url: str, product_id: str):
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """{
                    product(id: "gid://shopify/Product/"""
                + product_id
                + """") {
                        id
                        featuredImage {
                            id
                            url
                        }
                        variants(first: 100) {
      edges {
        node {
          id
          title
          displayName
          availableForSale
          inventoryQuantity
          selectedOptions {
            name
            value
          }
          price
          image {
            url
            id
          }
        }
      }
    }
                    }
                }"""
            )
            result = json.loads(data)
            default_image = (
                result.get("data", {}).get("product", {}).get("featuredImage", {})
            )
            variants = (
                result.get("data", {})
                .get("product", {})
                .get("variants", {})
                .get("edges", [])
            )
            for index, variant in enumerate(variants):
                image = variant.get("node", {}).get("image", {})
                if not image:
                    result["data"]["product"]["variants"]["edges"][index]["node"][
                        "image"
                    ] = default_image

            return result

    def get_all_variants_for_order(self, shop_url: str, order_id: str) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """{
                order(id: "gid://shopify/Order/"""
                + order_id
                + """") {
                            id
    name
    displayFinancialStatus
    displayFulfillmentStatus
    customer {
      id
      firstName
      lastName
      displayName
      email
      phone
    }
    lineItems(first: 10) {
      edges {
        node {
          id
          image {
            id
            url
          }
          quantity
          currentQuantity
          variant {
            displayName
            selectedOptions {
              name
              value
            }
          }
          product {
            id
            variants(first: 20) {
              edges {
                node {
                  id
                  displayName
                  selectedOptions {
                    name
                    value
                  }
                  image {
                    url
                    id
                  }
                }
              }
            }
          }
        }
      }
    }
                        }
                    }"""
            )
            return json.loads(data)

    def begin_order_edit(self, shop_url: str, order_id: str) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """
                mutation
                    beginEdit {
                        orderEditBegin(id: "gid://shopify/Order/"""
                + order_id
                + """"){
                            calculatedOrder{
                                id
                            }
                        }
                    }
                """
            )
            return json.loads(data)

    def add_variant_to_order(
        self, shop_url: str, calc_order_id: str, variant_id: str, quantity: int
    ) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """
                mutation
                    addVariantToOrder {
                        orderEditAddVariant(id: "gid://shopify/CalculatedOrder/"""
                + calc_order_id
                + """", variantId: "gid://shopify/ProductVariant/"""
                + variant_id
                + """", quantity: """
                + str(quantity)
                + """) {
                            calculatedOrder {
                                id
                                addedLineItems(first:5) {
                                    edges {
                                        node {
                                            id
                                            quantity
                                        }
                                    }
                                }
                            }
                            userErrors {
                                field
                                message
                            }
                        }
                    }
                """
            )
            return json.loads(data)

    def set_line_item_quantity(
        self, shop_url: str, calc_order_id: str, line_item_id: str, quantity
    ) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """
                mutation
                    increaseLineItemQuantity {
                        orderEditSetQuantity(id: "gid://shopify/CalculatedOrder/"""
                + calc_order_id
                + """", lineItemId: "gid://shopify/CalculatedLineItem/"""
                + line_item_id
                + """", quantity: """
                + str(quantity)
                + """) {
                            calculatedOrder {
                                id
                                addedLineItems(first: 5) {
                                    edges {
                                        node {
                                            id
                                            quantity
                                        }
                                    }
                                }
                            }
                            userErrors {
                                field
                                message
                            }
                        }
                    }
                """
            )
            return json.loads(data)

    def get_calculated_order_by_id(self, shop_url: str, calc_order_id: str) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """
                query {
                    node(id: "gid://shopify/CalculatedOrder/"""
                + calc_order_id
                + """") {
                        ... on CalculatedOrder {
                            id
                            taxLines {
                                priceSet {
                                    shopMoney {
                                        amount
                                    }
                                }
                            }
                            totalOutstandingSet {
                                shopMoney {
                                    amount
                                }
                            }
                            totalPriceSet {
                                shopMoney {
                                    amount
                                    currencyCode
                                }
                            }
                            subtotalPriceSet {
                                shopMoney {
                                    amount
                                    currencyCode
                                }
                            }

                            cartDiscountAmountSet {
                                shopMoney {
                                    amount
                                    currencyCode
                                }
                            }
                            lineItems(first: 10) {
                                edges {
                                    node {
                                        id
                                        image {
                                            url
                                        }
                                        quantity
                                        originalUnitPriceSet {
                                            shopMoney {
                                                amount
                                                currencyCode
                                            }
                                        }
                                        discountedUnitPriceSet {
                                            shopMoney {
                                                amount
                                                currencyCode
                                            }
                                        }
                                        calculatedDiscountAllocations {
                                            allocatedAmountSet {
                                                shopMoney {
                                                  amount
                                                  currencyCode
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                """
            )
            return json.loads(data)

    def commit_edit_order(self, shop_url: str, calc_order_id: str) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """
                mutation
                    commitEdit {
                        orderEditCommit(id: "gid://shopify/CalculatedOrder/"""
                + calc_order_id
                + """", notifyCustomer: true, staffNote: "Order was updated by chad") {
                            order {
                                id
                            }
                            userErrors {
                                field
                                message
                            }
                        }
                    }
                """
            )
            return json.loads(data)

    def refund_owed_amount(
        self,
        shop_url: str,
        order_id: str,
        refund_amount: str,
        gateway: str,
        parent_id: str,
    ) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """
                mutation {
                    refundCreate(
                        input: {
                            orderId: "gid://shopify/Order/"""
                + order_id
                + """"
                                        notify: true
                                        note: "Customer edited order to a cheaper item. Refund was issued on the price difference between original item ordered and the new item."
                                        transactions: [
                                            {
                                                amount: """
                + refund_amount
                + """
                                                orderId: "gid://shopify/Order/"""
                + order_id
                + '''"
                                                kind: REFUND
                                                gateway: "'''
                + gateway
                + '''"
                                                parentId: "'''
                + parent_id
                + """"
                                            }
                                        ]
                                    }
                                ) {
                                    userErrors {
                                        field
                                        message
                                    }
                                    refund {
                                        id
                                    }
                                }
                            }
                            """
            )
            return json.loads(data)

    def send_order_invoice(self, shop_url: str, order_id: str) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """
                    mutation {
                        orderInvoiceSend(
                            id: "gid://shopify/Order/"""
                + order_id
                + """"
                        ) {
                            order {
                                id
                            }
                            userErrors {
                                field
                                message
                            }
                        }
                    }
                """
            )
            return json.loads(data)

    def get_only_order_status(self, shop_url: str, order_id: str):
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """{
                order(id: "gid://shopify/Order/"""
                + order_id
                + """") {
                    id
                    name
                    createdAt
                    updatedAt
                    displayFinancialStatus
                    displayFulfillmentStatus
                    totalOutstandingSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    customer {
                        id
                        firstName
                        lastName
                        displayName
                        email
                        phone
                    }
                }
            }"""
            )

            return json.loads(data)

    def get_order_id_by_fulfillment_id(
        self, shop_url: str, fulfillment_id: str
    ) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """
                query {
                    fulfillment(id: "gid://shopify/Fulfillment/"""
                + fulfillment_id
                + """") {
                        order {
                            id
                        }
                    }
                }
                """
            )
            return json.loads(data)

    def create_webhook(self, shop_url: str, topic: str, callback_url: str) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """
                mutation {
                    webhookSubscriptionCreate(
                        topic: """
                + topic
                + """
                        webhookSubscription: {
                            format: JSON,
                            callbackUrl: "https://"""
                + callback_url.replace("https://", "")
                + """"
                        }
                    )
                    {
                        userErrors {
                            field
                            message
                        }
                        webhookSubscription {
                            id
                        }
                    }
                }
                """
            )
            return json.loads(data)

    def make_unfulfilled_order_on_hold(
        self, shop_url: str, fulfillment_order_id: str, reason_notes: str
    ) -> dict:
        temp_session = self.initiate_temporary_session(shop_url)
        with temp_session:
            data = shopify.GraphQL().execute(
                """
                mutation {
                    fulfillmentOrderHold(
                        fulfillmentHold: {
                            reason: OTHER
                            reasonNotes: """
                + '''"'''
                + reason_notes
                + '''"'''
                + """
                            notifyMerchant: false
                        },
                        id: "gid://shopify/FulfillmentOrder/"""
                + fulfillment_order_id
                + """"
                    )
                    {
                        fulfillmentOrder {
                            id
                            status
                            requestStatus
                            fulfillmentHolds {
                                reason
                                reasonNotes
                            }
                        }
                        userErrors {
                            field
                            message
                        }
                    }
                }
                """
            )
            return json.loads(data)
