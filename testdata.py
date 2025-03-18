from naledi.naledimodels import MncUser, MncDepartment
from naledi.extensions import db

admin_municipality = 2  # Set manually for debugging

officials = (
    db.session.query(
        MncUser.mnc_user_id,
        MncUser.mncfname,
        MncUser.mnclname,
        MncUser.mncemail,
        MncUser.mnctitle,
        MncDepartment.deptname
    )
    .join(MncDepartment, MncUser.deptid == MncDepartment.deptid)
    .filter(MncUser.municipalid == admin_municipality)
    .all()
)

print(officials)  # Should return data