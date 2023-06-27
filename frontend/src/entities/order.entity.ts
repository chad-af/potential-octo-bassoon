import {
  type GraphQLList,
  type Money,
  type ShopifyListResponse,
  type ShopifyResponse,
} from '~/app/base/entities/shopify.entity';

export type OrderStatus =
  | 'ORDERED'
  | 'SHIPPED'
  | 'DELIVERED'
  | 'REFUNDED'
  | 'CANCELATION_REQUESTED'
  | 'PAYMENT_PENDING'
  | 'ON_HOLD'
  | 'DELIVERY_EXCEPTION'
  | 'DELIVERY_FAILURE';

export type TrackingStatus =
  | 'DELIVERED'
  | 'SHIPPED'
  | 'DELIVERY_EXCEPTION'
  | 'DELIVERY_FAILURE';

export type OrderListResponse = ShopifyListResponse<
  'orders',
  {
    id: string;
    name: string;
    createdAt: string;
    chadFulfillmentStatus: string;
    displayFinancialStatus: string;
    displayFulfillmentStatus: string;
    shippedAt?: string;
    deliveredAt?: string;
    totalPriceSet: {
      shopMoney: Money;
    };
    currentTotalPriceSet: {
      shopMoney: Money;
    };
    lineItems: GraphQLList<{
      id: string;
      name: string;
      image: {
        url: string;
      } | null;
      currentQuantity: number;
    }>;
    trackingDetails?: TrackingDetail | null;
  }
>;

export type OrderDetailResponse = ShopifyResponse<
  'order',
  {
    id: string;
    name: string;
    createdAt: string;
    displayFinancialStatus: string;
    displayFulfillmentStatus: string;
    customer: {
      id: string;
      firstName: string;
      lastName: string;
      displayName: string;
      email: string;
      phone: string;
    };
    fulfillments: Array<{
      trackingInfo: Array<{
        number: string;
        company: string;
        url: string;
      }>;
    }>;
    shippingAddress: {
      id: string;
      address1: string;
      address2: string;
      city: string;
      company: string;
      country: string;
      countryCodeV2: string;
      name: string;
      firstName: string;
      lastName: string;
      phone: string;
      province: string | null;
      provinceCode: string | null;
      zip: string;
      latitude: number | null;
      longitude: number | null;
      coordinatesValidated: boolean;
    } | null;
    totalShippingPriceSet: {
      shopMoney: Money;
    };
    totalTaxSet: {
      shopMoney: Money;
    };
    currentTotalTaxSet: {
      shopMoney: Money;
    };
    totalPriceSet: {
      shopMoney: Money;
    };
    currentTotalPriceSet: {
      shopMoney: Money;
    };
    totalDiscountsSet: {
      shopMoney: Money;
    };
    currentTotalDiscountsSet: {
      shopMoney: Money;
    };
    refundedPriceSet?: {
      shopMoney: Money;
    };
    lineItems: GraphQLList<{
      id: string;
      name: string;
      image: {
        url: string;
      } | null;
      currentQuantity: number;
      discountedTotalSet: {
        shopMoney: Money;
      };
      discountedUnitPriceSet: {
        shopMoney: Money;
      };
      variant: {
        id: string;
        title: string;
        displayName: string;
        selectedOptions: VariantSelectOption[];
      };
      product: {
        id: string;
        totalVariants: number;
      };
    }>;
    chadFulfillmentStatus: string;
    isLate: boolean;
    lateThreshold: string;
    cancelationRequest?: {
      isFailed: boolean;
      reason: string;
    };
    originalOrder: {
      totalShippingPriceSet: {
        shopMoney: Money;
      };
      currentTotalTaxSet: {
        shopMoney: Money;
      };
      currentTotalPriceSet: {
        shopMoney: Money;
      };
      currentTotalDiscountsSet: {
        shopMoney: Money;
      };
      lineItems: Array<{
        id: string;
        name: string;
        image: {
          url: string;
        } | null;
        currentQuantity: number;
        discountedTotalSet: {
          shopMoney: Money;
        };
        discountedUnitPriceSet: {
          shopMoney: Money;
        };
      }>;
    };
    shippedAt: string | null;
    deliveredAt: string | null;
    trackingDetails?: TrackingDetail | null;
    trackingInfoErrorMessage: string | null;
  }
>;

interface TrackingDetail {
  statusMilestone: string;
  chadStatus: string;
  estimatedDeliveryDate: string | null;
  deliveredDateTime: string | null;
  lastEvent?: {
    occurrenceDatetime: string;
    location: string | null;
    geoCoordinates?: {
      latitude: number;
      longitude: number;
    };
  };
}

export interface VariantSelectOption {
  name: string;
  value: string | number | boolean;
}

export interface PreviousLineItem {
  id: string;
  name: string;
  quantity: number;
  discountedUnitPriceSet: {
    shopMoney: Money;
  };
  image: {
    url: string;
  } | null;
  variantId: string;
}

export type OrderDetailData = NonNullable<OrderDetailResponse['data']['order']>;

export type OrderDetailAddress = NonNullable<
  OrderDetailResponse['data']['order']['shippingAddress']
>;
