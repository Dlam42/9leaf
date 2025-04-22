from django.contrib import admin
from .models import User_Client
from .models import Customer

from .models import Customer_Description
from .models import Customer_Rating
from .models import Worker
from .models import Worker_Description
from .models import Worker_Rating
from .models import Location
from .models import Jobs
from .models import Request

# Register your models here.
admin.site.register(User_Client)
admin.site.register(Customer)
admin.site.register(Customer_Description)
admin.site.register(Customer_Rating)
admin.site.register(Worker)
admin.site.register(Worker_Description)
admin.site.register(Worker_Rating)
admin.site.register(Location)
admin.site.register(Jobs)
admin.site.register(Request)

