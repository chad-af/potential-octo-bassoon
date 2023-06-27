import { produce } from 'immer';
import { toast } from 'react-hot-toast/headless';

import {
  type OrderDetailData,
  type OrderStatus,
  type TrackingStatus,
} from './order.entity';

import { type useContactUs } from '~/app/contact-us/entities/contact-us.entity';
import { type OrderDetailStatusProps } from '~/app/order/components/order-detail-status';

export const DeliveryStatus = {
  ordered: 0,
  shipped: 1,
  delivered: 2,
  exception: 2,
  failed: 3,
} as const satisfies Record<string, number>;

export const DeliveryStatusLabels = {
  default: ['Ordered', 'Shipped', 'Delivered'],
  hasException: ['Ordered', 'Shipped', 'Exception', 'Delivered'],
  failed: ['Ordered', 'Shipped', 'Exception', 'Failed'],
};

export interface OrderDetailPageState {
  label: string;
  statusBar?: OrderDetailStatusProps['statusBar'];
  alerts?: OrderDetailStatusProps['alerts'];
  actions?: { label: string; to: string; eventType?: string }[];
}

export const TrackingLabel = {
  DELIVERED: 'Delivered',
  SHIPPED: 'Shipped',
  DELIVERY_EXCEPTION: 'Delivery exception',
  DELIVERY_FAILURE: 'Delivery failed',
} as const satisfies Record<TrackingStatus, string>;

/**
 * Generates common props for the `OrderDetailStatus` component.
 *
 * TODO: Change to hooks and use useMemo on most of the implementation
 */
// eslint-disable-next-line sonarjs/cognitive-complexity
export function commonOrderDetailStatusProps({
  data,
  orderStatus,
  pageState,
  navigateContactUs,
}: {
  data: OrderDetailData;
  orderStatus: OrderStatus;
  pageState: OrderDetailPageState;
  navigateContactUs: ReturnType<typeof useContactUs>['navigateContactUs']; // TODO: Remove this when use hooks
}) {
  const trackingUrlDisplay =
    orderStatus !== 'ORDERED'
      ? data.fulfillments[0]?.trackingInfo[0]
      : undefined;

  // TODO: Change to useMemo when we already use data router
  const alerts = produce(pageState.alerts ?? [], (draft) => {
    if (
      orderStatus === 'DELIVERY_EXCEPTION' &&
      draft[0]?.action?.type === 'anchor'
    ) {
      draft[0].action.href = trackingUrlDisplay?.url;

      const exceptionStatus = data.trackingDetails?.statusMilestone;
      if (exceptionStatus === 'available_for_pickup') {
        draft[0].title = 'Available for pickup';
        draft[0].body =
          "Your order is being held at a pickup point such as your local courier's office. Click on the button below to check location.";
        draft[0].action.label = 'View location details';
      }
    } else if (
      orderStatus === 'DELIVERY_FAILURE' &&
      draft[0]?.action?.type === 'button'
    ) {
      draft[0].action.onClick = () => {
        navigateContactUs({
          problemCategory: 'POST_PURCHASE/DELIVERY/LATE/NOT_DELIVERED',
        });
      };
    }
  });

  // TODO: Change to useMemo when we already use data router
  const statusBar = produce(pageState.statusBar, (draft) => {
    if (!draft) return;

    // Handle DELIVERED status with a previous exception status
    if (
      orderStatus === 'DELIVERED' &&
      data.trackingInfoErrorMessage?.toLowerCase() === 'status not available'
    ) {
      draft.labels = DeliveryStatusLabels.hasException;
      draft.active = 3;
    }
  });

  function getTrackingLabelDate(
    trackingDetails: NonNullable<typeof data.trackingDetails>
  ) {
    const trackingStatus = trackingDetails.chadStatus as TrackingStatus;

    let label: string = TrackingLabel[trackingStatus];
    let usedDate: string | undefined | null;

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

    return {
      label,
      date: usedDate ? new Date(usedDate) : undefined,
    };
  }

  // TODO: Change to useMemo when we already use data router
  function getTracking(): OrderDetailStatusProps['tracking'] {
    const trackingDetails = data?.trackingDetails;

    if (!trackingDetails) {
      if (trackingUrlDisplay) {
        return { trackingUrlDisplay };
      } else {
        return undefined;
      }
    }

    const { label, date } = getTrackingLabelDate(trackingDetails);
    const location = trackingDetails.lastEvent?.location ?? undefined;
    const map = trackingDetails.lastEvent?.geoCoordinates;

    const trackingStatus = trackingDetails.chadStatus as TrackingStatus;

    if (
      !location &&
      !map &&
      !date &&
      trackingUrlDisplay &&
      !['DELIVERY_EXCEPTION', 'DELIVERY_FAILURE'].includes(trackingStatus)
    ) {
      toast.error(
        "We're experiencing a temporary outage and can't find tracking info. Click on the tracking URL to find your package.",
        { id: 'error-tracking-details', className: 'multiline' }
      );
    }

    return {
      label,
      date,
      location,
      map,
      trackingUrlDisplay,
    };
  }

  return {
    alerts,
    statusBar,
    tracking: getTracking(),
  };
}
