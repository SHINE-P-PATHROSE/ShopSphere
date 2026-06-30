from .models import Cart

def cart_context(request):
    # Prevent errors during migration or if database isn't ready
    try:
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                # We don't force session creation on every request, just try to get it
                session_key = ''
            if session_key:
                cart, _ = Cart.objects.get_or_create(session_key=session_key)
            else:
                cart = None

        return {
            'global_cart': cart,
            'cart_items_count': cart.total_items if cart else 0,
            'cart_count': cart.total_items if cart else 0,
        }
    except Exception:
        return {
            'global_cart': None,
            'cart_items_count': 0,
        }
