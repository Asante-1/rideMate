from django.core import serializers
import json
from accounts.models import User
import time
from core import settings
from backend.models import Agency, Booking, Seat, Transaction, Trip
from django.shortcuts import render
from django.views import View
from api.serializers import BookingSerializer, RegisterSerializer, TripSerializer, UserSerializer
from rest_framework import generics, permissions
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from django.contrib.auth import login


class OverviewAPI(APIView):
    '''endpoint for all endpoints'''

    def get(self, request, *args, **kwargs):
        end_points = {
            'overview': '/api/',
            'login': '/api/login/',
            'sign-up': '/api/sign-up/',
            'all-trips': '/api/all-trips/',
            'trips-today': '/api/trips-today/',
            'search-trips': '/api/search-trips/',
            'bookings': '/api/bookings/',
            'book-trip': '/api/book-trip/',
        }
        return Response(end_points)


class AllTripsAPI(APIView):
    '''endpoint for getting all trips available'''
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        trips = Trip.objects.all()
        print(trips)
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)


class TripsTodayAPI(APIView):
    '''endpoint for getting all trips for the day'''
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        trips = Trip.objects.filter(date=time.strftime("%Y-%m-%d"))
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)


class SearchTripsAPI(APIView):
    '''endpoint for getting all trips for the day'''
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        agency_id = request.data['agency']
        source = request.data['source']
        destination = request.data['destination']
        agency = Agency.objects.filter(id=int(agency_id)).first()
        # date format: YYYY-MM-DD
        date = request.data['date']
        trips = Trip.objects.filter(date=date, source=source, destination=destination, vehicle__agency=agency)  # noqa
        serializer = TripSerializer(trips, many=True)
        if trips:
            return Response(serializer.data)
        else:
            return Response({"error": "No trips found for your search query"}, status=status.HTTP_404_NOT_FOUND)  # noqa


class BookTripAPI(APIView):
    '''endpoint to book trips'''
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        trip_id = request.data['trip']
        user_id = request.data['user']
        seat_ids = request.data['seats']
        trip = Trip.objects.filter(id=int(trip_id)).first()
        user = User.objects.filter(id=int(user_id)).first()
        # seat = Seat.objects.filter(id=int(seat_id)).first()
        booking = Booking.objects.create(user=user, trip=trip)
        booking.save()
        for seat_id in seat_ids:
            try:
                seat = Seat.objects.filter(id=int(seat_id)).first()
                booking.seats.add(seat)
                booking.save()
                seat.is_booked = True
                seat.save()
            except Exception as e:
                booking.delete()
                return Response({"error": e}, status=status.HTTP_404_NOT_FOUND)
        serialized = serializers.serialize(queryset=[booking], format='json')
        return Response({"booking": serialized}, status=status.HTTP_201_CREATED)


class UserBookings(APIView):
    '''endpoint to get all trips booked by the user'''
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user_id = request.data['user']
        user = User.objects.filter(id=int(user_id)).first()
        bookings = Booking.objects.filter(user=user)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)


class LoginAPI(KnoxLoginView):
    '''Login api endpoint'''
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return super(LoginAPI, self).post(request, format=None)


class SignUpAPI(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": UserSerializer(user).data,
            "token": AuthToken.objects.create(user)[1]
        })
