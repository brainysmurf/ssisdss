from dss.importers.db_importer import PostgresDBImporter
from ssis_dss.moodle.MoodleInterface import MoodleInterface
import ssis_dss_settings
from collections import defaultdict

class MoodleImporter(PostgresDBImporter, MoodleInterface):
    _settings = ssis_dss_settings['SSIS_DB']
    reader = None

    def readin(self):
        """
        """
        return []

class MoodleStudentsImporter(MoodleImporter):
    def readin(self):
        users = self.import_students_with_links('studentsALL')

        for student, parent in users:
            yield {
                'idnumber':student.idnumber, 
                'firstname':student.firstname, 
                'lastname':student.lastname,
                'auth': student.auth,
                'username': student.username,
                'homeroom': student.department,
                'parents': [parent.idnumber],
            }

class MoodleParentsImporter(MoodleImporter):
    def readin(self):
        # Build cohort information to be used below

        parents = self.users_enrolled_in_this_cohort('parentsALL')

        for parent in parents:

            yield {
                'idnumber':parent.idnumber, 
                'firstname':parent.firstname, 
                'lastname':parent.lastname,
                'auth': parent.auth,
                'username': parent.username,
                'email': parent.email,
                'homeroom': parent.department,
            }

class MoodleTeachersImporter(MoodleImporter):
    def readin(self):
        for user in self.users_enrolled_in_this_cohort('teachersALL'):
            #idnumber _dbid lastfirst email title status active dunno
            yield {
                'idnumber': user.idnumber,
                'firstname': user.firstname,
                'lastname':user.lastname,
                'username':user.username,
                'email': user.email,
            }

# Users is a hybrid

class MoodleParentChildLinkImporter(MoodleImporter):
    def readin(self):
        users = self.import_parents_with_links('parentsALL')
        for parent, student in users:
            yield {
                'idnumber': student.idnumber,
                'links': set([parent.idnumber])
            }
            yield {
                'idnumber': parent.idnumber,
                'links': set([student.idnumber])
            }


class StrandedUsersTable(MoodleImporter):
    def readin(self):
        for user in self.get_rows_in_table('users'):
            if user.idnumber and not self._tree.users.get(user.idnumber):
                yield {
                    'idnumber': user.idnumber,
                    'object': user
                }
        return []

class MoodleCohortsImporter(MoodleImporter):
    def readin(self):
        for user_idnumber, cohort_idnumber in self.get_cohorts():
            user = self._tree.users.get(user_idnumber)
            if not user:
                continue
            yield {
                'idnumber': cohort_idnumber,
                'members': [user_idnumber],
            }

class MoodleScheduleImporter(MoodleImporter):
    """
    This is just a placeholder. Autosend side needs to import the schedule from which to derive enrollments
    But Moodle already has enrollments, and doesn't need the schedule.
    """ 
    def readin(self):
        for schedule in self.bell_schedule():
            course, idnumber, username, role, group, group_name = schedule
            user = self._tree.users.get(idnumber)

            yield {
                'user_idnumber': idnumber,
                'course': course,
                'group': group,
                'role': role
            }

class MoodleCourseImporter(MoodleImporter):
    def readin(self):   
        for item in self.get_teaching_learning_courses():
            yield {
                'idnumber': item.idnumber,
                'moodle_shortcode': item.idnumber,
                'name': item.fullname,
                '_dbid': item.database_id
            }

class MoodleGroupImporter(MoodleImporter):
    # FIXME: Have a setting that allows to filter out
    # def filter_out(self, **kwargs):
    #     return len(kwargs['idnumber'].split('-')) != 3

    def readin(self):
        for group_id, group_idnumber, course_idnumber, user_idnumber in self.get_groups():
            if '-' in group_idnumber:
                split = group_idnumber.split('-')
                if len(split) == 4:
                    grade = split[-2]
                elif len(split) == 3:
                    # may not have been migrated yet
                    grade = ''
                teacher = split[0]
                section = split[-1]
            else:
                section = ''
                grade = ''
                teacher = ''

            if not group_idnumber:
                # Manual groups can be created without idnumber, in which case we should just move on
                continue

            yield {
                'idnumber': group_idnumber,
                'grade': grade,
                'section': section,
                '_short_code': '',
                '_id': group_id,
                'course': course_idnumber,
                'members': set([user_idnumber])
            }

        for group, course in self.get_all_groups():
            if not group.idnumber:
                continue

            if '-' in group.idnumber:
                split = group.idnumber.split('-') 
                section = group.idnumber.split('-')[-1]
                if len(split) == 4:
                    grade = split[-2]
                else:
                    grade = ''
            else:
                section = ''

            yield {
                'idnumber': group.idnumber,
                'grade': grade,
                'section': section,
                'course': course.idnumber,
                '_id': group.id,
                'members': set()
            }


class MoodleEnrollmentsImporter(MoodleImporter):

    def readin(self):
        """

        TODO: This is wrong, maybe just do another SQL 

        """
        for key in self._tree.schedule.keys():
            schedule = self._tree.schedule.get(key)
            user_idnumber = schedule.user_idnumber
            course = schedule.course
            group = schedule.group
            role = schedule.role

            yield {
                'idnumber': user_idnumber,
                'courses': [course],
                'groups': ['' if group is None else group],
                'roles': [role]
            }

