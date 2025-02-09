from .models import Ride, Payment
from naledi.naledimodels import User

def match_ride(commuter_id, pickup_location, dropoff_location):
    """
    Match a commuter with a nearby driver.
    """
    # Find a nearby available driver (simplified example)
    driver = User.query.filter_by(role='driver').first()
    if not driver:
        return None, "No available drivers"

    # Create a new ride
    ride = Ride(
        pickup_location=pickup_location,
        dropoff_location=dropoff_location,
        commuter_id=commuter_id,
        driver_id=driver.id
    )
    ride.save()

    return ride, "Ride matched successfully"

def process_payment(ride_id, amount):
    """
    Process a payment for a ride.
    """
    # Create a new payment record
    payment = Payment(
        ride_id=ride_id,
        amount=amount
    )
    payment.save()

    # Simulate payment processing (e.g., call a payment gateway)
    payment.status = 'completed'
    payment.save()

    return payment, "Payment processed successfully"

def notify_user(user_id, message):
    """
    Send a notification to a user (simplified example).
    """
    user = User.query.get(user_id)
    if not user:
        return False, "User not found"

    # Simulate sending a notification (e.g., email, SMS, push notification)
    print(f"Notification sent to {user.email}: {message}")
    return True, "Notification sent successfully"

#mtcginbg a ride example
from ..core.services import match_ride

# Commuter requests a ride
ride, message = match_ride(commuter_id=1, pickup_location="123 Main St", dropoff_location="456 Elm St")
print(message)  # "Ride matched successfully"

# Process the payment for the ride

from ..core.services import process_payment

# Process payment for a ride
payment, message = process_payment(ride_id=1, amount=25.0)
print(message)  # "Payment processed successfully"


# Notify the user about the ride

from ..core.services import notify_user

# Notify a user
success, message = notify_user(user_id=1, message="Your ride has been matched!")
print(message)  # "Notification sent successfully"
