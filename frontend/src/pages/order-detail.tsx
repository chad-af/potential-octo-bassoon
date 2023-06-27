import { useParams, useSearchParams } from 'react-router-dom';
import { toast } from 'react-hot-toast/headless';
import { useState } from 'react';
import * as Sentry from '@sentry/react';
import { produce } from 'immer';

import { type OrderStatus } from '~/app/order/entities/order.entity';
import { type Money } from '~/app/base/entities/shopify.entity';
import {
  DeliveryStatus,
  DeliveryStatusLabels,
  type OrderDetailPageState,
  commonOrderDetailStatusProps,
} from '~/app/order/entities/order-detail.entity';
import { CHeader } from '~/app/base/components/navigation/c-header';
import { BasePage } from '~/app/common/components/base-page';
import { ServiceTag } from '~/app/common/components/service-tag';
import { OrderDetailStatus } from '~/app/order/components/order-detail-status';
import { OrderDetailSummary } from '~/app/order/components/order-detail-summary';
import { OrderDetailActions } from '~/app/order/components/order-detail-actions';
import { ProductDisplay } from '~/app/order/components/product-display';
import { useOrderDetail } from '~/app/order/queries/order.query';
import { displayShopifyImage } from '~/app/utils/format.util';
import { currencyFormat, displayMoney } from '~/app/utils/currency.util';
import { OrderDetailLoading } from '~/app/order/components/loading/order-detail.loading';
import { getMerchantValue } from '~/app/merchant/merchant.util';
import { BottomSheetOriginalOrder } from '~/app/order/components/bottom-sheet-original-order';
import { useContactUs } from '~/app/contact-us/entities/contact-us.entity';

const actions = {
  whereIsMyOrder: {
    label: 'Where is my order',
    to: 'tracking',
    eventType: 'WHERE_IS_MY_ORDER',
  },
  changeShippingAddress: {
    label: 'Change shipping address',
    to: 'change-shipping-address',
    eventType: 'CHANGE_SHIPPING_ADDRESS',
  },
  applyCouponCode: {
    label: 'Apply coupon code',
    to: 'apply-coupon-code',
    eventType: 'APPLY_COUPON_CODE',
  },
  wrongShippingAddress: {
    label: 'My shipping address is wrong',
    to: 'contact-us-wrong-address',
    eventType: 'WRONG_SHIPPING_ADDRESS',
  },
  defectiveItems: {
    label: 'My item(s) is defective',
    to: 'defective',
    eventType: 'DEFECTIVE_ITEMS',
  },
  missingItems: {
    label: 'My order arrived but some items are missing',
    to: 'missing',
    eventType: 'MISSING_ITEMS',
  },
  returnItems: {
    label: getMerchantValue({
      'all-citizens': 'Return / Exchange item(s)',
      default: 'Return item(s)',
    }),
    to: 'return-exchange',
    eventType: 'RETURN_ITEMS',
  },
  viewReturnLabel: {
    label: 'View return label / instructions',
    to: 'view-return-label',
    eventType: 'VIEW_RETURN_LABEL',
  },
  changeVariant: {
    label: 'Ordered the wrong size / color',
    to: 'edit-order',
    eventType: 'CHANGE_VARIANT',
  },
  cancelOrder: {
    label: 'I want to cancel my order',
    to: 'cancel',
    eventType: 'CANCEL_ORDER',
  },
} as const;

const pageStates: Record<OrderStatus, OrderDetailPageState> = {
  ORDERED: {
    label: 'Ordered',
    statusBar: {
      labels: DeliveryStatusLabels.default,
      active: DeliveryStatus.ordered,
    },
    actions: [
      actions.whereIsMyOrder,
      actions.changeShippingAddress,
      actions.changeVariant,
      actions.cancelOrder,
      // actions.applyCouponCode,
    ],
  },
  SHIPPED: {
    label: 'Shipped',
    statusBar: {
      labels: DeliveryStatusLabels.default,
      active: DeliveryStatus.shipped,
    },
    actions: [
      actions.whereIsMyOrder,
      actions.wrongShippingAddress,
      // actions.applyCouponCode,
    ],
  },
  DELIVERED: {
    label: 'Delivered',
    statusBar: {
      labels: DeliveryStatusLabels.default,
      active: DeliveryStatus.delivered,
    },
    actions: getMerchantValue({
      'all-citizens': [
        actions.whereIsMyOrder,
        actions.returnItems,
        actions.missingItems,
        actions.defectiveItems,
      ],
      default: [
        actions.whereIsMyOrder,
        actions.defectiveItems,
        actions.missingItems,
        actions.returnItems,
      ],
    }),
  },
  REFUNDED: {
    label: 'Refunded',
    alerts: [
      {
        type: 'success',
        title: 'Order canceled',
        body: 'We have processed your refund. Please check your original method of payment.',
      },
    ],
  },
  CANCELATION_REQUESTED: {
    label: 'Cancelation requested',
    statusBar: {
      labels: DeliveryStatusLabels.default,
      active: DeliveryStatus.ordered,
    },
    actions: [
      actions.whereIsMyOrder,
      actions.changeShippingAddress,
      // actions.applyCouponCode,
    ],
  },
  PAYMENT_PENDING: {
    label: 'Pending payment',
    actions: [
      actions.whereIsMyOrder,
      actions.changeShippingAddress,
      actions.changeVariant,
      actions.cancelOrder,
      // actions.applyCouponCode,
    ],
    alerts: [
      {
        type: 'warning',
        title: 'Pending payment',
        body: 'You have edited your order to include an item that is more expensive than what you initially ordered.\n\nMake payment within 3 days or your order will be canceled and refunded.',
        action: {
          type: 'button',
          label: 'View original order',
        },
      },
    ],
  },
  ON_HOLD: {
    label: 'On hold',
    actions: [
      actions.whereIsMyOrder,
      actions.changeShippingAddress,
      actions.cancelOrder,
    ],
    alerts: [
      {
        type: 'warning',
        title: 'Order placed on hold',
        body: "The top-up payment wasn't completed for the item you added, which is more expensive that what you initially ordered.\n\nA Happiness Hero will contact you within 2 business days (excluding weekends and holidays) with next steps.",
        action: {
          type: 'button',
          label: 'View original order',
        },
      },
    ],
  },
  DELIVERY_EXCEPTION: {
    label: 'Delivered',
    statusBar: {
      labels: DeliveryStatusLabels.hasException,
      active: DeliveryStatus.exception,
      barColor: 'yellow',
    },
    actions: [
      actions.whereIsMyOrder,
      actions.wrongShippingAddress,
      // actions.applyCouponCode,
    ],
    alerts: [
      {
        type: 'warning',
        title: 'Delivery exception',
        body: 'The courier was unable to deliver this order. Check to see if they missed you and left a note.',
        action: {
          type: 'anchor',
          label: 'View tracking info',
        },
      },
    ],
  },
  DELIVERY_FAILURE: {
    label: 'Delivered',
    statusBar: {
      labels: DeliveryStatusLabels.failed,
      active: DeliveryStatus.failed,
      barColor: 'red',
    },
    actions: [actions.whereIsMyOrder],
    alerts: [
      {
        type: 'error',
        title: 'Delivery failed',
        body: 'Your order is being returned to sender. Click on the button below to get more help.',
        action: {
          type: 'button',
          label: 'Contact us',
        },
      },
    ],
  },
};

export function PageOrderDetail() {
  const { orderId } = useParams();
  const { data } = useOrderDetail(orderId!);

  const [searchParams] = useSearchParams();
  const orderName = data?.name ?? searchParams.get('orderName');

  const [openBottomSheet, setOpenBottomSheet] = useState(false);

  const { navigateContactUs } = useContactUs();

  const jsx_header = (
    <CHeader title={`Order ${orderName}`} backNavOverride="/orders" />
  );

  if (!data) {
    return (
      <BasePage header={jsx_header} padding="bottomOnly">
        <OrderDetailLoading />
      </BasePage>
    );
  }

  let orderStatus: OrderStatus;
  if (data.chadFulfillmentStatus in pageStates) {
    orderStatus = data.chadFulfillmentStatus as keyof typeof pageStates;
  } else {
    Sentry.captureException(
      new Error(`State "${data.chadFulfillmentStatus}" doesn't exist`)
    );
    toast.error(
      'Oops! Our server has a temporary error\nPlease try again later',
      { id: 'error-order-detail', className: 'multiline' }
    );
    return null;
  }

  const pageState = pageStates[orderStatus];

  const { alerts, statusBar, tracking } = commonOrderDetailStatusProps({
    data,
    orderStatus,
    pageState,
    navigateContactUs,
  });

  const combinedAlerts = produce(alerts, (draft) => {
    if (
      ['PAYMENT_PENDING', 'ON_HOLD'].includes(orderStatus) &&
      draft[0]?.action?.type === 'button'
    ) {
      draft[0].action.onClick = () => setOpenBottomSheet(true);
    }

    if (data.cancelationRequest?.isFailed && orderStatus !== 'DELIVERED') {
      draft.push({
        position: 'end',
        type: 'error',
        title: "Your order couldn't be canceled",
        body: 'The order shipped out a little too fast. Please wait for the order to be delivered before initiating a return.',
      });
    }
  });

  const discount = Number(data.currentTotalDiscountsSet.shopMoney.amount);

  /**
   * The function creates a logic to determine whether to apply a `lineThrough` props to the
   * `ServiceTag` component based on the `amountOrMoney` parameter and the `orderStatus`.
   * @param {number | Money} amountOrMoney - It is a parameter that can accept either a number or a
   * Money object.
   * @returns either the string 'price' or undefined.
   */
  function lineThroughServiceTag(amountOrMoney: number | Money) {
    if (orderStatus !== 'REFUNDED') return undefined;

    let amount: number;
    if (typeof amountOrMoney === 'number') amount = amountOrMoney;
    else amount = Number(amountOrMoney.amount);

    if (amount > 0) return 'price';
    else return undefined;
  }

  return (
    <BasePage header={jsx_header}>
      <OrderDetailStatus
        alerts={combinedAlerts}
        statusBar={statusBar}
        tracking={tracking}
      />

      <OrderDetailSummary
        orderNumber={data.name}
        badge={pageState.label}
        totalPrice={data.currentTotalPriceSet.shopMoney}
        orderPlaced={new Date(data.createdAt)}
        shippingAddress={data.shippingAddress}
      />

      <div className="mt-6 pt-6 b-t-1 b-shade-80">
        <ProductDisplay
          products={data.lineItems.edges.map(({ node }) => ({
            id: node.id,
            name: node.name,
            quantity: node.currentQuantity,
            image:
              node.image &&
              displayShopifyImage({ url: node.image!.url, width: 80 }),
            price: displayMoney(node.discountedTotalSet.shopMoney),
          }))}
          lineThrough={orderStatus === 'REFUNDED'}
        />

        <div className="flex flex-col gap-2 px-5 mt-6">
          {discount > 0 && (
            <ServiceTag
              label="Discount"
              price={currencyFormat(
                -Math.abs(discount),
                data.currentTotalDiscountsSet.shopMoney.currencyCode
              )}
              lineThrough={lineThroughServiceTag(discount)}
            />
          )}

          <ServiceTag
            label="Shipping"
            price={displayMoney(data.totalShippingPriceSet.shopMoney)}
            lineThrough={lineThroughServiceTag(
              data.totalShippingPriceSet.shopMoney
            )}
          />

          <ServiceTag
            label="Taxes"
            price={displayMoney(data.currentTotalTaxSet.shopMoney)}
            lineThrough={lineThroughServiceTag(
              data.currentTotalTaxSet.shopMoney
            )}
          />

          <ServiceTag
            label={orderStatus === 'REFUNDED' ? 'Amount refunded' : 'Total'}
            price={
              orderStatus === 'REFUNDED' && data.refundedPriceSet
                ? currencyFormat(
                    Number(data.refundedPriceSet.shopMoney.amount),
                    data.refundedPriceSet.shopMoney.currencyCode
                  )
                : displayMoney(data.currentTotalPriceSet.shopMoney)
            }
            labelBold
            className="mt-2"
          />
        </div>
      </div>

      <OrderDetailActions actions={pageState.actions} />

      {data.originalOrder ? (
        <BottomSheetOriginalOrder
          open={openBottomSheet}
          onClose={() => setOpenBottomSheet(false)}
          data={data.originalOrder}
        />
      ) : null}
    </BasePage>
  );
}
