import { cartService } from "../services/cartService.js";
import { userEventService, EVENT_TYPES } from "../services/userEventService.js";

export const createCartSlice = (set, get) => ({
  cart: [],
  aiDiscount: 0,
  isCartSyncing: false,
  activityCount: 0,

  setAiDiscount: async (discount) => {
    set({ aiDiscount: discount });
    const token = get().token;
    if (token) {
      try {
        await cartService.applyDiscount(discount);
      } catch (err) {
        console.warn("[CartSlice] Failed to sync discount with backend:", err);
      }
    }
  },

  trackActivity: () => {
    const { activityCount, sendAiEvent } = get();
    const newCount = (activityCount || 0) + 1;
    if (newCount >= 3) {
      if (sendAiEvent) sendAiEvent("activity_threshold_reached");
      set({ activityCount: 0 });
    } else {
      set({ activityCount: newCount });
    }
  },

  fetchBackendCart: async () => {
    const token = get().token;
    if (!token) return;

    set({ isCartSyncing: true });
    try {
      const items = await cartService.getCartItems();
      if (Array.isArray(items)) {
        const mappedItems = items.map((item) => ({
          id: item.product_id || item.product?.id || item.id,
          name: item.product?.name || item.name || "Product",
          price: item.price ?? item.product?.price ?? 0,
          original_price: item.original_price ?? item.product?.price ?? item.price ?? 0,
          discount_percentage: item.discount_percentage || 0,
          discounted_price: item.discounted_price || null,
          qty: item.quantity ?? item.qty ?? 1,
          size: item.size || null,
          color: item.color || null,
          image_url: item.product?.image_url || item.image_url || "",
        }));

        set({ cart: mappedItems, isCartSyncing: false });
      } else {
        set({ isCartSyncing: false });
      }
    } catch (err) {
      console.warn("[CartSlice] Backend cart sync error:", err);
      set({ isCartSyncing: false });
    }
  },

  addToCart: async (product, qty = 1, size = null, color = null) => {
    get().trackActivity();

    // 1. Optimistic local update
    set((state) => {
      const existing = state.cart.find(
        (item) => item.id === product.id && item.size === size && item.color === color
      );
      if (existing) {
        return {
          cart: state.cart.map((item) =>
            item.id === product.id && item.size === size && item.color === color
              ? { ...item, qty: item.qty + qty }
              : item
          ),
        };
      }
      return {
        cart: [...state.cart, { ...product, qty, size, color }],
      };
    });

    // 2. Telemetry tracking
    userEventService.trackEvent(EVENT_TYPES.ADD_TO_CART, product.id);

    // 3. Backend persistence if authenticated
    const token = get().token;
    if (token) {
      try {
        await cartService.addItem({
          productId: product.id,
          quantity: qty,
          size,
        });
      } catch (err) {
        console.warn("[CartSlice] Failed to sync added item with backend:", err);
      }
    }
  },

  removeFromCart: async (id, size = null, color = null) => {
    get().trackActivity();

    // 1. Optimistic local update
    set((state) => ({
      cart: state.cart.filter(
        (item) => !(item.id === id && item.size === size && item.color === color)
      ),
    }));

    // 2. Telemetry tracking
    userEventService.trackEvent(EVENT_TYPES.REMOVE_FROM_CART, id);

    // 3. Backend sync
    const token = get().token;
    if (token) {
      try {
        await cartService.removeItem({
          productId: id,
          size,
        });
      } catch (err) {
        console.warn("[CartSlice] Failed to sync removed item with backend:", err);
      }
    }
  },

  updateCartQty: async (id, size = null, color = null, qty = 1) => {
    const validatedQty = Math.max(1, qty);

    // 1. Local update
    set((state) => ({
      cart: state.cart.map((item) =>
        item.id === id && item.size === size && item.color === color
          ? { ...item, qty: validatedQty }
          : item
      ),
    }));

    // 2. Backend sync
    const token = get().token;
    if (token) {
      try {
        await cartService.updateItem({
          productId: id,
          quantity: validatedQty,
          size,
        });
      } catch (err) {
        console.warn("[CartSlice] Failed to sync updated quantity with backend:", err);
      }
    }
  },

  clearCart: async () => {
    set({ cart: [], aiDiscount: 0 });
    const token = get().token;
    if (token) {
      try {
        await cartService.clearCart();
      } catch (err) {
        console.warn("[CartSlice] Failed to clear backend cart:", err);
      }
    }
  },
});
