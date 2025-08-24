import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred , {
    'databaseURL' : 'https://faceattendacnerealtime-f717b-default-rtdb.firebaseio.com/'
})

ref  = db.reference('Students')
data = {
    '321654' :
        {
            'name' : "Murtaza Hassan",
            'major' :'Robotics',
            'starting_year' :2017 ,
            'total_attendance' :6 , 
            'standing' :'G',
            'year' :4 ,
            'last_attendance_time' :'2022-12-11 00:54:34'
        },
        '852741' :
        {
            'name' : "Emly Blunt",
            'major' :'Economics',
            'starting_year' :2018 ,
            'total_attendance' :12 , 
            'standing' :'B',
            'year' :2 ,
            'last_attendance_time' :'2022-12-11 00:54:34'
        },
           '963852' :
        {
            'name' : "Elon Mask",
            'major' :'physics',
            'starting_year' :2020 ,
            'total_attendance' :7 , 
            'standing' :'G',
            'year' :2 ,
            'last_attendance_time' :'2022-12-11 00:54:34'
        },
        '109234' :
        {
            'name' : "Alhussien Ayman",
            'major' :'Software Engineer',
            'starting_year' :2022 ,
            'total_attendance' :0 , 
            'standing' :'G',
            'year' :3 ,
            'last_attendance_time' :'2022-12-11 00:54:34'
        },
}

for key, value in data.items() :
    ref.child(key).set(value)