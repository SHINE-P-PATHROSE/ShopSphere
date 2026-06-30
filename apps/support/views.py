"""Support web views."""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views import View

from .models import SupportTicket, TicketMessage


class TicketListView(LoginRequiredMixin, ListView):
    model = SupportTicket
    template_name = 'support/ticket_list.html'
    context_object_name = 'tickets'

    def get_queryset(self):
        qs = SupportTicket.objects.all()
        if self.request.user.role != 'ADMIN':
            qs = qs.filter(user=self.request.user)
        return qs.order_by('-created_at')


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = SupportTicket
    template_name = 'support/ticket_create.html'
    fields = ['subject', 'category', 'priority', 'order']
    success_url = reverse_lazy('support:list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = SupportTicket
    template_name = 'support/ticket_detail.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        qs = SupportTicket.objects.prefetch_related('messages')
        if self.request.user.role != 'ADMIN':
            qs = qs.filter(user=self.request.user)
        return qs


class TicketReplyView(LoginRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(SupportTicket, pk=pk)
        if ticket.user != request.user and request.user.role != 'ADMIN':
            messages.error(request, 'Permission denied.')
            return redirect('support:list')
        TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            body=request.POST.get('body', ''),
            is_staff_reply=request.user.role == 'ADMIN',
        )
        if request.user.role == 'ADMIN':
            ticket.status = 'IN_PROGRESS'
            ticket.save(update_fields=['status'])
        return redirect('support:detail', pk=pk)
