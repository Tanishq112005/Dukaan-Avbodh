import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { createAuthSlice } from './createAuthSlice'
import { createProductSlice } from './createProductSlice'
import { createCartSlice } from './createCartSlice'
import { createChatSlice } from './createChatSlice'
import { ThumbsDownIcon } from 'lucide-react';

export const useStore = create(
  persist(
    (...a) => ({
      ...createAuthSlice(...a),
      ...createProductSlice(...a),
      ...createCartSlice(...a),
      ...createChatSlice(...a),
    }),
    {
      name: 'dukaan-store',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        cart: state.cart,
        aiDiscount: state.aiDiscount,
        aiMessages: state.aiMessages,
        aiMessagesLastUpdated: state.aiMessagesLastUpdated,
        comboOffer: state.comboOffer,
        isAgentOpen: state.isAgentOpen,
        guestId: state.guestId,
        thread : state.threadId 
      })
    }
  )
)
