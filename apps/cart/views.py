from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from .models import Cart, CartItem
from apps.products.models import ProductVariant

class CartView(View):
    template_name = 'cart/cart.html'

    def get_request_cart(self, request):
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        return cart

    def get(self, request):
        cart = self.get_request_cart(request)
        cart_items = cart.items.filter(saved_for_later=False)
        saved_items = cart.items.filter(saved_for_later=True)
        return render(request, self.template_name, {
            'cart': cart,
            'cart_items': cart_items,
            'saved_items': saved_items,
        })

class AddToCartView(View):
    def post(self, request):
        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1))
        variant = get_object_or_404(ProductVariant, id=variant_id)

        if not variant.is_in_stock:
            messages.error(request, 'This product variant is out of stock.')
            return redirect('products:detail', slug=variant.product.slug)

        if variant.stock < quantity:
            messages.error(request, f'Only {variant.stock} units available in stock.')
            return redirect('products:detail', slug=variant.product.slug)

        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, variant=variant)
        if not created:
            if variant.stock < (cart_item.quantity + quantity):
                messages.error(request, f'Cannot add more units. Only {variant.stock} units in stock, and you have {cart_item.quantity} in your cart.')
                return redirect('cart:cart')
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        messages.success(request, 'Item added to cart.')
        return redirect('cart:cart')

class UpdateCartItemView(View):
    def post(self, request, item_id):
        if request.user.is_authenticated:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        else:
            cart_item = get_object_or_404(
                CartItem, id=item_id, cart__session_key=request.session.session_key
            )
        quantity = int(request.POST.get('quantity', 1))

        if quantity <= 0:
            cart_item.delete()
            return JsonResponse({'success': True, 'message': 'Item removed from cart.'})

        if cart_item.variant.stock < quantity:
            return JsonResponse({'success': False, 'message': f'Only {cart_item.variant.stock} units available.'})

        cart_item.quantity = quantity
        cart_item.save()

        return JsonResponse({
            'success': True,
            'message': 'Cart updated.',
            'line_total': float(cart_item.line_total),
            'subtotal': float(cart_item.cart.subtotal),
        })


class RemoveCartItemView(View):
    def post(self, request, item_id):
        if request.user.is_authenticated:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        else:
            cart_item = get_object_or_404(
                CartItem, id=item_id, cart__session_key=request.session.session_key
            )
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
        return redirect('cart:cart')

class ToggleSaveForLaterView(View):
    def post(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.saved_for_later = not cart_item.saved_for_later
        cart_item.save()
        msg = 'Item saved for later.' if cart_item.saved_for_later else 'Item moved to cart.'
        messages.success(request, msg)
        return redirect('cart:cart')
