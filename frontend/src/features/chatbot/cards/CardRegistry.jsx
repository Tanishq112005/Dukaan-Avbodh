import React from "react";
import { RecommendationCard } from "./RecommendationCard";
import { NegotiationCard } from "./NegotiationCard";
import { CartUpdateCard } from "./CartUpdateCard";
import { PaymentCard } from "./PaymentCard";
import { OrderConfirmationCard } from "./OrderConfirmationCard";

const CARD_COMPONENTS = {
  recommendation: RecommendationCard,
  negotiation: NegotiationCard,
  cart_update: CartUpdateCard,
  payment: PaymentCard,
  order_confirmed: OrderConfirmationCard,
};

export function AiCard({ card, onProductClick, onPayClick, onAction }) {
  if (!card || !card.type) return null;
  const Component = CARD_COMPONENTS[card.type];
  if (!Component) return null;

  return (
    <Component
      data={card.data}
      onProductClick={onProductClick}
      onPayClick={onPayClick}
      onAction={onAction}
    />
  );
}

export {
  RecommendationCard,
  NegotiationCard,
  CartUpdateCard,
  PaymentCard,
  OrderConfirmationCard,
};
