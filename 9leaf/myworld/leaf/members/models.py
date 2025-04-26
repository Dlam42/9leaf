from django.db import models

# Create your models here.
class User_Client(models.Model):
    user_id = models.AutoField(primary_key=True, unique=True)
    user_name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    phone_num = models.CharField(max_length=20, unique=True)
    address = models.TextField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    geo_location = models.CharField(max_length=255)
    unit_apt_num = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    payment_option = models.CharField(max_length=50, choices=[('Paypal', 'Paypal'), ('Debit/Credit', 'Debit/Credit')], default='Paypal')
    identification = models.CharField(max_length=255, default="none")
    dark_mode = models.BooleanField(default=False)
    language = models.CharField(default="English", max_length=50)
    is_admin = models.BooleanField(default=False)

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True, unique=True)
    user_id = models.OneToOneField(User_Client, on_delete=models.CASCADE)

class Customer_Description(models.Model):
    cstmr_descr_id = models.AutoField(primary_key=True)
    description = models.TextField()
    customer_id = models.OneToOneField(Customer, on_delete=models.CASCADE)

class Customer_Rating(models.Model):
    class RatingChoices(models.IntegerChoices):
        ONE_STAR=1, "1_STAR"
        TWO_STAR=2, "2_STAR"
        THREE_STAR=3, "3_STAR" 
        FOUR_STAR=4, "4_STAR" 
        FIVE_STAR=5, "5_STAR"

    cstmr_rate_id = models.AutoField(primary_key=True)
    rate = models.IntegerField(choices=RatingChoices.choices)
    user_id = models.ForeignKey(User_Client, on_delete=models.CASCADE)

class Worker(models.Model):
    worker_id = models.AutoField(primary_key=True)
    user_id = models.OneToOneField(User_Client, on_delete=models.CASCADE)

class Worker_Description(models.Model):
    worker_description_id = models.AutoField(primary_key=True)
    description = models.TextField()
    customer_id = models.OneToOneField(Customer, on_delete=models.CASCADE)

class Worker_Rating(models.Model):
    class RatingChoices(models.IntegerChoices):
        ONE_STAR=1, "1_STAR"
        TWO_STAR=2, "2_STAR"
        THREE_STAR=3, "3_STAR" 
        FOUR_STAR=4, "4_STAR" 
        FIVE_STAR=5, "5_STAR"

    worker_rate_id = models.AutoField(primary_key=True)
    rate = models.IntegerField(choices=RatingChoices.choices)
    user_id = models.ForeignKey(User_Client, on_delete=models.CASCADE)
    

class Location(models.Model):
    location_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User_Client, on_delete=models.CASCADE)
    location_name = models.CharField(max_length=255)
    location_address = models.TextField()
    location_city = models.CharField(max_length=255)
    location_state = models.CharField(max_length=255)
    location_unit_num = models.CharField(max_length=255)
    location_zip_code = models.CharField(max_length=255)
    geo_location = models.CharField(max_length=255)


class Jobs(models.Model):
    job_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User_Client, on_delete=models.CASCADE)
    job_name = models.CharField(max_length=255)
    start_time = models.CharField(max_length=255)
    tool = models.CharField(max_length=255)
    job_description = models.TextField()
    job_price = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    geo_location = models.CharField(max_length=255)
    unit_apt_num = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=255)
    duration = models.CharField(max_length=255)
    personal_business = models.CharField(max_length=255)
    job_size = models.CharField(max_length=255)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)

class Request(models.Model):
    request_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User_Client, on_delete=models.CASCADE)
    job_number = models.CharField(max_length=10, unique=True, blank=True, null=True)  # New field for job number

    request_name = models.CharField(max_length=255)
    start_time = models.CharField(max_length=255)
    tool = models.CharField(max_length=255)
    request_description = models.TextField()
    request_price = models.CharField(max_length=255)
    
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    geo_location = models.CharField(max_length=255)
    unit_apt_num = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=255)
    duration = models.CharField(max_length=255)
    personal_business = models.CharField(max_length=255)
    request_size = models.CharField(max_length=255)
    people_amount = models.CharField(max_length=255)
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    rejection_reason = models.TextField(null=True, blank=True)

# We'll use Firebase directly for the messaging system
# This is just a placeholder class for migration purposes
class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    sender = models.CharField(max_length=255)  # Will store user_id (Firebase UID)
    receiver = models.CharField(max_length=255)  # Will store user_id (Firebase UID)
    subject = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

