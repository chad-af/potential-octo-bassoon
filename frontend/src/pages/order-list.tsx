import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';

import {
  type OrderListResponse,
  type OrderStatus,
  type TrackingStatus,
} from '~/app/order/entities/order.entity';
import { API } from '~/api';
import { useAuthUser } from '~/app/auth/auth.util';
import { CHeader } from '~/app/base/components/navigation/c-header';
import { BasePage } from '~/app/common/components/base-page';
import { OrderCard } from '~/app/common/components/order-card';
import { displayShopifyImage, getShopifyId } from '~/app/utils/format.util';
import { OrderListLoading } from '~/app/order/components/loading/order-list.loading';

type OrderListData = OrderListResponse['data']['orders']['edges'][0]['node'];

const ORDER_STATUS_LABEL: Record<OrderStatus, string> = {
  ORDERED: 'Ordered',
  SHIPPED: 'Shipped',
  DELIVERED: 'Delivered',
  REFUNDED: 'Refunded',
  CANCELATION_REQUESTED: 'Cancelation requested',
  PAYMENT_PENDING: 'Pending payment',
  ON_HOLD: 'On hold',
  DELIVERY_EXCEPTION: 'Delivery exception',
  DELIVERY_FAILURE: 'Delivery failed',
};

// eslint-disable-next-line sonarjs/cognitive-complexity
function getStatus(data: OrderListData) {
  let label = '';

  const chadStatus = data.chadFulfillmentStatus;
  if (chadStatus in ORDER_STATUS_LABEL) {
    label = ORDER_STATUS_LABEL[chadStatus as keyof typeof ORDER_STATUS_LABEL];
  }

  let usedDate: string | undefined | null;

  const trackingDetails = data.trackingDetails;
  if (trackingDetails) {
    const trackingStatus = trackingDetails.chadStatus as TrackingStatus;

    if (trackingStatus === 'SHIPPED') {
      usedDate = data.shippedAt;

      if (trackingDetails.statusMilestone === 'out_for_delivery') {
        label = 'Out for delivery';
      } else if (trackingDetails.estimatedDeliveryDate) {
        label = 'Est. delivery';
        usedDate = trackingDetails.estimatedDeliveryDate;
      }
    } else if (trackingStatus === 'DELIVERED') {
      usedDate = trackingDetails.deliveredDateTime ?? data.deliveredAt;
    } else if (
      trackingStatus === 'DELIVERY_EXCEPTION' &&
      trackingDetails.statusMilestone === 'available_for_pickup'
    ) {
      label = 'Available for pickup';
      usedDate = trackingDetails.lastEvent?.occurrenceDatetime;
    }
  } else {
    if (data.chadFulfillmentStatus === 'SHIPPED') {
      usedDate = data.shippedAt;
    } else if (data.chadFulfillmentStatus === 'DELIVERED') {
      usedDate = data.deliveredAt;
    }
  }

  if (label && usedDate) {
    return `${label} ${format(new Date(usedDate), 'MMM d, yyyy')}`;
  } else {
    return label;
  }
}

function useFetchOrders() {
  const user = useAuthUser();

  return useQuery({
    queryKey: ['orders'],
    queryFn: async () => {
      const { data } = await API.get(
        `shopify/order/email/${user.email}`
      ).json<OrderListResponse>();

      const orders = data.orders.edges.map((order) => {
        const { node } = order;

        const orderId = getShopifyId(node.id);

        const images = node.lineItems.edges
          .filter((item) => item.node.image !== null)
          .map((item) =>
            displayShopifyImage({ url: item.node.image!.url, width: 80 })
          );

        return {
          orderId,
          status: getStatus(node),
          name: node.name,
          totalPrice: node.currentTotalPriceSet.shopMoney,
          orderPlaced: new Date(node.createdAt),
          images,
        };
      });

      // Sort DESCENDING by Order Placed
      return orders.sort(
        (a, b) => b.orderPlaced.getTime() - a.orderPlaced.getTime()
      );
    },
  });
}

export function PageOrderList() {
  const { data: orders } = useFetchOrders();

  return (
    <BasePage
      padding="none"
      header={<CHeader title="Your orders" backNavOverride="/home" />}
    >
      {!orders ? (
        <OrderListLoading />
      ) : (
        orders.map((order, index) => (
          <OrderCard
            key={order.orderId}
            {...order}
            background={index % 2 === 0 ? 'light' : 'dark'}
          />
        ))
      )}
    </BasePage>
  );
}
