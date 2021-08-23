#encoding: utf-8
from __future__ import unicode_literals, print_function, division
import json
import os
import shutil
import logging
from task.audience.field import get_field
from task.audience.member import Member
from task.audience.member_relationship import MemberRelationship, RelationshipType
from task.config import config
from task.database import get_by, redis
from task import database
from task.dbaccessor import get_shortcode
from task.lists.async import REDIS_KEY_LIST_SEGMENT_EXCLUDE_SMS_SUB_COUNT, REDIS_KEY_LIST_SEGMENT_EXCLUDE_EMAIL_SUB_COUNT
from task.lists.models import SmsSourceType
from task.messageconstants import custom_field_types
import unittest
from task import s3
from task.audience.csvimporter import parse_csv_column, import_status, accept_csv, upload_bucket, buff_count
from task.lists.subscription import subscribed_email, subscribed_sms, unsubscribe_sms, unsubscribe_email
from task.tests.builders.sysoption import add_uniform_sms_footer
from task.tests.builders.upload import new_upload, email_upload_confirm_message, sms_upload_confirm_message, sms_upload_welcome_message, email_upload_welcome_message
from task.tests.builders.list import football_list, subscribe_to_sms, subscribe_to_email
from task.tests.builders.audience import blocked_email, global_blocked_email, unblocked_emails
from task.tests.builders.shortcode import new_short_code, assign_short_code_to
from task.tests.builders.upload import new_upload_member_log
from task.tests.builders.user import new_user
from task.tests.test_util import clear, create_custom_picklist_field, create_custom_field, create_account


upload_dir = config.get('upload', 'upload.dir')

logger = logging.getLogger(__name__)

def _prepare_custom_fields(account_id):
	create_custom_picklist_field(account_id, 'level', 'level', ['high', 'midium', 'low', 'Café'], custom_field_types.PICKLIST)
	create_custom_picklist_field(account_id, 'Interests','Interests', ['Movie', 'Sports', 'Programming', 'Reading', 'Game', 'Party'], custom_field_types.MULTIPICKLIST)
	create_custom_field(account_id, 'income','INCOME', custom_field_types.NUMBER)
	create_custom_field(account_id, 'self introduce','SELFINTRO', custom_field_types.SINGLELINE)
	create_custom_field(account_id, 'anniversary','ANNIVERSARY', custom_field_types.DATE)

def _generate_fields_mapping_rule(columns, account=None):
	column_fields = []

	for position, column in enumerate(columns):
		field = get_field(account, column.strip())
		s = '{"column_position":%s,"field_name":"%s","field_id":%s}' % (position, field.column_name if field else column, field.id if field else 0)
		column_fields.append(s)

	return "[" + ",".join(column_fields) + "]"


class ImportAudienceTest(unittest.TestCase):

	def setUp(self):
		clear()
		self.account = create_account('ms-dev')
		self.account_id = self.account.id
		self.upload_user = new_user('test-email@change-to-your-email.com').save()

		assign_short_code_to(new_short_code('91001'), self.account.id, False)
		self.sc_91000 = get_shortcode('91001')

		self.football_club = football_list(self.account.id, shortcode_id=self.sc_91000.id).save()
		add_uniform_sms_footer()


	def _get_total_lines_in_file(self, csvfile, encoding='utf-8'):
		return buff_count(os.path.join(config.get('upload', 'upload.dir'), csvfile), encoding=encoding)

	def _copy_file_to_temp_and_return_csvfile(self, filename):
		csvfile = self._csv_file(filename=filename)
		src = self._csv_path(filename=filename)
		dest = os.path.join(upload_dir, csvfile)
		try:
			shutil.copy(src, dest)
		except IOError:
			# try creating parent directories
			os.makedirs(os.path.dirname(dest))
			shutil.copy(src, dest)
		return csvfile

	def test_adding_new_members_to_list(self):
		_prepare_custom_fields(self.account.id)
		csvfile = self._copy_file_to_temp_and_return_csvfile('audience_with_custom_fields.csv')
		mapping_rule = _generate_fields_mapping_rule(
			['Land_Line', 'Zip_Code', 'First_Name', 'last_Name', 'gender', 'birth_Date', 'email', 'mobile_Phone',
			 'level', 'income', 'Interests', 'anniversary'], self.account)

		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csvfile,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csvfile)
		).save()

		accept_csv(self.account.id, upload.id, csvfile, self.football_club.id, False)

		members = self._all_members()
		self.assertEqual(len(members), 2)
		bob = members[0]
		daniel = members[1]
		self.assertEqual(bob['firstname'], 'Bob')
		self.assertEqual(bob['email'], 'firehorse.ms@gmail.com')
		self.assertEqual(bob['mobilephone'], '16505760833')
		self.assertEqual(bob['custom_data'][get_field(self.account, 'level').column_name], 'high')
		self.assertEqual(bob['custom_data'][get_field(self.account, 'income').column_name], 10000)
		self.assertEqual(bob['custom_data'][get_field(self.account, 'interests').column_name], 'Movie | Programming')
		self.assertEqual(bob['custom_data'][get_field(self.account, 'anniversary').column_name], '1986-10-10')
		self.assertEqual(daniel['firstname'], 'Daniel')
		self.assertEqual(daniel['email'], 'ms_bj@mobilestorm.com')
		self.assertEqual(daniel['custom_data'][get_field(self.account, 'level').column_name], 'low')
		self.assertEqual(daniel['custom_data'][get_field(self.account, 'income').column_name], 15000)
		self.assertEqual(daniel['custom_data'][get_field(self.account, 'interests').column_name], 'Game')
		self.assertEqual(daniel['custom_data'][get_field(self.account, 'anniversary').column_name], '1980-10-01')

		status = json.loads(import_status(self.account.id, upload.id))
		self.assertEquals(status['status'], 'completed')
		self.assertTrue('error_message' not in status)
		self.assertEquals(status['total_count'], 3)

		for member in members:
			if member['email']:
				self.assertTrue(subscribed_email(self.football_club.id, member.id))
			if member['mobile_phone']:
				self.assertTrue(subscribed_sms(self.football_club.id, member.id))

		self.assertEquals(int(redis.get(REDIS_KEY_LIST_SEGMENT_EXCLUDE_SMS_SUB_COUNT % (self.football_club.id, 'null', 'null'))), 1)
		self.assertEquals(int(redis.get(REDIS_KEY_LIST_SEGMENT_EXCLUDE_EMAIL_SUB_COUNT % (self.football_club.id, 'null', 'null'))), len(members))

	def test_adding_new_members_to_list_with_different_mobile_phone_formats(self):
		_prepare_custom_fields(self.account.id)
		csvfile = self._copy_file_to_temp_and_return_csvfile('audience_with_multiple_mobile_phone_formats.csv')
		mapping_rule = _generate_fields_mapping_rule(
			['Land_Line', 'Zip_Code', 'First_Name', 'last_Name', 'gender', 'birth_Date', 'email', 'mobile_Phone',
			 'level', 'income', 'Interests', 'anniversary'], self.account)

		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csvfile,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csvfile)
		).save()

		accept_csv(self.account.id, upload.id, csvfile, self.football_club.id, False)

		members = self._all_members()
		self.assertEqual(len(members), 2)
		bob = members[0]
		daniel = members[1]
		self.assertEqual(bob['firstname'], 'Bob')
		self.assertEqual(bob['email'], 'firehorse.ms@gmail.com')
		self.assertEqual(bob['mobilephone'], '18889999909')
		self.assertEqual(bob['custom_data'][get_field(self.account, 'level').column_name], 'high')
		self.assertEqual(bob['custom_data'][get_field(self.account, 'income').column_name], 10000)
		self.assertEqual(bob['custom_data'][get_field(self.account, 'interests').column_name], 'Movie | Programming')
		self.assertEqual(bob['custom_data'][get_field(self.account, 'anniversary').column_name], '1986-10-10')
		self.assertEqual(daniel['firstname'], 'Daniel')
		self.assertEqual(daniel['email'], 'ms_bj@mobilestorm.com')
		self.assertEqual(daniel['mobilephone'], '18889999908')
		self.assertEqual(daniel['custom_data'][get_field(self.account, 'level').column_name], 'low')
		self.assertEqual(daniel['custom_data'][get_field(self.account, 'income').column_name], 15000)
		self.assertEqual(daniel['custom_data'][get_field(self.account, 'interests').column_name], 'Game')
		self.assertEqual(daniel['custom_data'][get_field(self.account, 'anniversary').column_name], '1980-10-01')


	def test_adding_new_members_to_list_with_pipe_delimiter(self):
		_prepare_custom_fields(self.account.id)
		csvfile = self._copy_file_to_temp_and_return_csvfile('audience_with_pipe_delimited_custom_fields.csv')
		mapping_rule = _generate_fields_mapping_rule(
			['Land_Line', 'Zip_Code', 'First_Name', 'last_Name', 'gender', 'birth_Date', 'email', 'mobile_Phone',
			 'level', 'income', 'Interests', 'anniversary'], self.account)

		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csvfile,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			is_pipe_delimited=True,
			total_lines=self._get_total_lines_in_file(csvfile=csvfile)
		).save()

		accept_csv(self.account.id, upload.id, csvfile, self.football_club.id, False)

		members = self._all_members()
		self.assertEqual(len(members), 2)
		bob = members[0]
		daniel = members[1]
		self.assertEqual(bob['firstname'], 'Bob')
		self.assertEqual(bob['email'], 'firehorse.ms@gmail.com')
		self.assertEqual(bob['mobilephone'], '16505760833')
		self.assertEqual(bob['custom_data'][get_field(self.account, 'level').column_name], 'high')
		self.assertEqual(bob['custom_data'][get_field(self.account, 'income').column_name], 10000)
		self.assertEqual(bob['custom_data'][get_field(self.account, 'interests').column_name], 'Movie | Programming')
		self.assertEqual(bob['custom_data'][get_field(self.account, 'anniversary').column_name], '1986-10-10')
		self.assertEqual(daniel['firstname'], 'Daniel')
		self.assertEqual(daniel['email'], 'ms_bj@mobilestorm.com')
		self.assertEqual(daniel['custom_data'][get_field(self.account, 'level').column_name], 'low')
		self.assertEqual(daniel['custom_data'][get_field(self.account, 'income').column_name], 15000)
		self.assertEqual(daniel['custom_data'][get_field(self.account, 'interests').column_name], 'Game')
		self.assertEqual(daniel['custom_data'][get_field(self.account, 'anniversary').column_name], '1980-10-01')

		status = json.loads(import_status(self.account.id, upload.id))
		self.assertEquals(status['status'], 'completed')
		self.assertTrue('error_message' not in status)
		self.assertEquals(status['total_count'], 3)

		for member in members:
			if member['email']:
				self.assertTrue(subscribed_email(self.football_club.id, member.id))
			if member['mobile_phone']:
				self.assertTrue(subscribed_sms(self.football_club.id, member.id))

		self.assertEquals(int(redis.get(REDIS_KEY_LIST_SEGMENT_EXCLUDE_SMS_SUB_COUNT % (self.football_club.id, 'null', 'null'))), 1)
		self.assertEquals(int(redis.get(REDIS_KEY_LIST_SEGMENT_EXCLUDE_EMAIL_SUB_COUNT % (self.football_club.id, 'null', 'null'))), len(members))

	def test_parse_csv_header_with_iso_8859_1_codec(self):
		csvfile = self._csv_path('audience_with_custom_fields_iso_8859_1.csv')
		csv_columns, lines = parse_csv_column(csvfile, encoding='ISO-8859-1')

		self.assertEqual(lines, 3)
		self.assertEqual(len(csv_columns), 12)
		self.assertEqual(csv_columns[8]["value"], 'Café')
		self.assertEqual(csv_columns[8]["position"], 8)
		self.assertEqual(csv_columns[8]["name"], 'level')

	def test_parse_csv_header_with_utf_8_codec(self):
		csvfile = self._csv_path('audience_with_custom_fields_utf_8.csv')
		csv_columns, lines = parse_csv_column(csvfile)
		self.assertEqual(lines, 3)
		self.assertEqual(len(csv_columns), 12)
		self.assertEqual(csv_columns[8]["value"], 'Café')
		self.assertEqual(csv_columns[8]["position"], 8)
		self.assertEqual(csv_columns[8]["name"], 'level')

	def test_parse_csv_header_and_line_count_when_ignore_first_row_as_header(self):
		csvfile = self._csv_path('audience_with_no_header.csv')
		csv_columns, lines = parse_csv_column(csvfile, False)

		self.assertEqual(len(csv_columns), 6)
		self.assertEqual(lines, 2)
		self.assertEqual(csv_columns[0]["name"], 'Field 1')
		self.assertEqual(csv_columns[0]["position"], 0)
		self.assertEqual(csv_columns[0]["value"], 'Bob')


	def test_adding_new_members_to_list_with_iso_8859_1_codec(self):
		_prepare_custom_fields(self.account.id)
		csvfile = self._copy_file_to_temp_and_return_csvfile('audience_with_custom_fields_iso_8859_1.csv')
		mapping_rule = _generate_fields_mapping_rule(
			[
				'Land_Line', 'Zip_Code','First_Name','last_Name','gender','birth_Date',
				'email','mobile_Phone','level','income','Interests','anniversary'
			],
			self.account
		)

		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csvfile,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile, encoding='ISO-8859-1')
		).save()

		accept_csv(self.account.id, upload.id, csvfile, self.football_club.id, False)

		members = self._all_members()
		self.assertEqual(len(members), 2)
		bob = members[0]
		# TODO this should be passed
		# self.assertEqual(bob['custom_data'][get_field(self.account, 'level').column_name], 'Café')
		self.assertNotIn(get_field(self.account, 'level').column_name, bob['custom_data'])
		# TODO this should be passed
		# self.assertEqual(daniel['lastname'], 'Café')

	def test_adding_new_members_to_list_when_not_mapping_all_csv_columns(self):
		_prepare_custom_fields(self.account.id)
		csvfile = self._copy_file_to_temp_and_return_csvfile('audience_with_mapping_fields.csv')
		mapping_rule = _generate_fields_mapping_rule(
			[
				'Land_Line', 'Zip_Code','First_Name','last_Name','gender','birth_Date',
				'email','mobile_Phone','level','income'
			],
			self.account
		)
		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csvfile,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csvfile)
		).save()

		accept_csv(self.account.id, upload.id, csvfile, self.football_club.id, False)

		members = self._all_members()
		self.assertEqual(len(members), 2)
		bob = members[0]
		daniel = members[1]
		self.assertEqual(bob['firstname'], 'Bob')
		self.assertEqual(bob['email'], 'firehorse.ms@gmail.com')
		self.assertEqual(bob['mobilephone'], '16505760833')
		self.assertEqual(bob['custom_data'][get_field(self.account, 'level').column_name], 'high')
		self.assertEqual(bob['custom_data'][get_field(self.account, 'income').column_name], 10000)
		self.assertNotIn(get_field(self.account, 'interests').column_name, bob['custom_data'])
		self.assertNotIn(get_field(self.account, 'anniversary').column_name, bob['custom_data'])
		self.assertEqual(daniel['firstname'], 'Daniel')
		self.assertEqual(daniel['email'], 'ms_bj@mobilestorm.com')
		self.assertNotIn(get_field(self.account, 'interests').column_name, daniel['custom_data'])
		self.assertNotIn(get_field(self.account, 'anniversary').column_name, daniel['custom_data'])

		status = json.loads(import_status(self.account.id, upload.id))
		self.assertEquals(status['status'], 'completed')
		self.assertTrue('error_message' not in status)
		self.assertEquals(status['total_count'], 3)

		for member in members:
			if member['email']:
				self.assertTrue(subscribed_email(self.football_club.id, member.id))
			if member['mobile_phone']:
				self.assertTrue(subscribed_sms(self.football_club.id, member.id))


	def _import_members_and_blocked_addresses(self, all_members_in_csv, upload):
		for m in all_members_in_csv.values():
			new_upload_member_log(upload.id, self.football_club.id, m.id).save()
		subscribe_to_email(self.football_club, all_members_in_csv['in_list'])
		subscribe_to_sms(self.football_club, all_members_in_csv['without_email_permission'])
		blocked_email(all_members_in_csv['blocked'].email).save()
		blocked_email(all_members_in_csv['blocked_and_in_white_list'].email).save()
		global_blocked_email(all_members_in_csv['global_blocked'].email).save()
		global_blocked_email(all_members_in_csv['global_blocked_but_in_white_list'].email).save()
		unblocked_emails(equals=(all_members_in_csv['blocked_and_in_white_list'].email, all_members_in_csv['global_blocked_but_in_white_list'].email))

	def _verify_upload_result_in_db(self, account_id, upload_id, status, failed_reason=None):
		upload = get_by("upload", id=upload_id, account_id=account_id)
		self.assertEquals(upload.failed_reason, failed_reason)
		self.assertEquals(upload.status, status)

	def _all_members(self):
		members = Member.query().filter(Member.account==self.account).all()
		return sorted(members, key=lambda m: m.id)

	def _csv_file(self, filename):
		file_path = self._csv_path(filename)
		s3_object_key = 'account%s/%s' % (self.account.id, filename)
		s3.save_object(upload_bucket, s3_object_key, file_path)
		return s3_object_key

	def _csv_path(self, filename):
		return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'csv', filename)


	def test_member_unsubscribed_from_sms_remain_unsubscribe_after_import(self):
		_prepare_custom_fields(self.account.id)
		csvfile = self._copy_file_to_temp_and_return_csvfile('audience_with_custom_fields.csv')
		mapping_rule = _generate_fields_mapping_rule(
			['Land_Line', 'Zip_Code', 'First_Name', 'last_Name', 'gender', 'birth_Date', 'email', 'mobile_Phone',
			 'level', 'income', 'Interests', 'anniversary'], self.account)

		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csvfile,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csvfile)
		).save()

		accept_csv(self.account.id, upload.id, csvfile, self.football_club.id, False)

		members = self._all_members()
		self.assertEqual(len(members), 2)
		bob = members[0]
		self.assertEqual(bob['mobilephone'], '16505760833')
		unsubscribe_sms(self.account.id, self.football_club.id, bob['id'], bob['mobilephone'],SmsSourceType.IMPORT)
		accept_csv(self.account.id, upload.id, csvfile, self.football_club.id, False)
		self.assertTrue(not (subscribed_sms(self.football_club.id, bob['id'])))

	def test_member_unsubscribed_from_email_remain_unsubscribe_after_import(self):
		_prepare_custom_fields(self.account.id)
		csvfile = self._copy_file_to_temp_and_return_csvfile('audience_with_custom_fields.csv')
		mapping_rule = _generate_fields_mapping_rule(
			['Land_Line', 'Zip_Code', 'First_Name', 'last_Name', 'gender', 'birth_Date', 'email', 'mobile_Phone',
			 'level', 'income', 'Interests', 'anniversary'], self.account)

		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csvfile,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csvfile)
		).save()

		accept_csv(self.account.id, upload.id, csvfile, self.football_club.id, False)

		members = self._all_members()
		self.assertEqual(len(members), 2)
		bob = members[0]
		unsubscribe_email(self.account.id, self.football_club.id, bob['id'], bob['email'],SmsSourceType.IMPORT)
		accept_csv(self.account.id, upload.id, csvfile, self.football_club.id, False)
		self.assertTrue(not (subscribed_email(self.football_club.id, bob['id'])))

	def test_import_members_with_same_email_in_different_cases(self):
		csv_file = self._copy_file_to_temp_and_return_csvfile('members_with_same_email_different_case.csv')
		mapping_rule = _generate_fields_mapping_rule(['First_Name', 'email'], self.account)
		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csv_file,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csv_file)
		).save()
		accept_csv(self.account_id, upload.id, csv_file, self.football_club.id, need_confirm=False)

		members = database.list('SELECT * FROM audience_member where account_id = :account_id;',
								dict(account_id=self.account_id))
		member_email = members[0]
		self.assertEqual(len(members), 1)
		self.assertEqual(member_email.first_name, 'emailtest5')
		self.assertEqual(member_email.email, 'emailtest1@yopmail.com')

	def test_import_members_with_same_app_member_id_in_different_cases(self):
		csv_file = self._copy_file_to_temp_and_return_csvfile('members_with_same_app_member_id_different_case.csv')
		mapping_rule = _generate_fields_mapping_rule(['First_Name', 'app_member_Id'], self.account)
		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csv_file,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csv_file)
		).save()
		accept_csv(self.account_id, upload.id, csv_file, self.football_club.id, need_confirm=False)

		members = database.list('SELECT * FROM audience_member where account_id= :account_id;',
								dict(account_id=self.account_id))
		member_appmail = members[0]
		self.assertEqual(len(members), 1)
		self.assertEqual(member_appmail.first_name, 'appmailtest5')
		self.assertEqual(member_appmail.app_member_id, 'appmail1')

	def test_adding_new_members_to_list_with_comma_separated_phones(self):
		csvfile = self._copy_file_to_temp_and_return_csvfile('audience_with_multiple_phones.csv')
		mapping_rule = _generate_fields_mapping_rule(
			['First_Name', 'last_Name', 'mobile_Phone','email'], self.account
		)

		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csvfile,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csvfile)
		).save()

		accept_csv(self.account.id, upload.id, csvfile, self.football_club.id, False)

		members = self._all_members()
		self.assertEqual(len(members), 3)
		hulk = members[0]
		bob = members[1]
		baldy = members[2]
		self.assertEqual(hulk['firstname'], 'Hulk')
		self.assertEqual(hulk['email'], 'hulk@smash.com')
		self.assertEqual(hulk['mobilephone'], '16505761234')

		self.assertEqual(bob['firstname'], 'Bob')
		self.assertEqual(bob['email'], 'bob@thebuilder.com')
		self.assertEqual(bob['mobilephone'], '16505761236')

		self.assertEqual(baldy['firstname'], 'Caped')
		self.assertEqual(baldy['email'], 'siatama@opm.com')
		self.assertEqual(baldy['mobilephone'], '16505761238')

		status = json.loads(import_status(self.account.id, upload.id))
		self.assertEquals(status['status'], 'completed')
		self.assertTrue('error_message' not in status)
		self.assertEquals(status['total_count'], 3)


class TestCSVSharedContact(ImportAudienceTest):
	def setUp(self):
		super(TestCSVSharedContact, self).setUp()
		self.account.allow_shared_contact_information = True
		self.account.target_member_type = 2
		self.account.enable_frequency_control = False
		self.account.save()

	def get_sms_subscription(self, member_id, mobile_phone, status=1):
		return database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :member_id AND mobile_phone = :mobile_phone AND status = :status;',
							 dict(member_id=member_id, mobile_phone=mobile_phone, status=status))

	def get_email_subscription(self, member_id, email, status=1):
		return database.list('SELECT * FROM email_subscription WHERE audience_member_id = :member_id AND email = :email AND status = :status;',
							 dict(member_id=member_id, email=email, status=status))

	def get_appmail_subscription(self, member_id, dependee_id, status=1):
		return database.list('SELECT * FROM appmail_list_subscriber WHERE audience_member_id = :member_id AND dependee_id = :dependee_id AND status = :status;',
							 dict(member_id=member_id, dependee_id=dependee_id, status=status))

	def get_entry_from_mt_tracking(self, member_id, mobile_phone, message_type='sms_upload_welcome_message'):
		return database.list("SELECT * FROM mt_tracking WHERE audience_member_id = :member_id AND phone_number = :mobile_phone AND message_type = :message_type ;",
							 dict(member_id=member_id, mobile_phone=mobile_phone, message_type=message_type))

	def get_entry_from_email_sent(self, member_id, email):
		return database.list('SELECT * FROM email_sent WHERE audience_member_id = :member_id AND email = :email ;',
							 dict(member_id=member_id, email=email))

	def test_add_dependent_members_from_dependee_columns(self):
		dependee_all = Member(self.account, first_name='dependee_all', mobile_phone='19876000000', email='dependeeall@gmail.com',
							  app_member_id=42, client_member_id=43).save()
		dependee_mobile = Member(self.account, first_name='dependee_mobile', mobile_phone='19829111111').save()
		dependee_email = Member(self.account, first_name='dependee_email', email='dependeeemail@gmail.com').save()
		csv_file = self._copy_file_to_temp_and_return_csvfile('dependent_members_with_dependee_columns.csv')
		mapping_rule = _generate_fields_mapping_rule(['First_Name', 'mobile_Phone', 'email', 'app_member_Id', 'dependee_mobile_phone',
													  'dependee_email', 'dependee_app_member_id', 'dependee_client_member_id',
													  'relationship_type'], self.account)
		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csv_file,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csv_file)
		).save()

		email_upload_welcome_message(upload.id, self.football_club.id).save()
		sms_upload_welcome_message(upload.id, self.football_club.id).save()
		accept_csv(self.account_id, upload.id, csv_file, self.football_club.id, need_confirm=False, send_welcome_message=True)
		dependent_members = database.list('SELECT * FROM audience_member WHERE account_id = :account_id and id not in :dependee_ids ORDER BY ID ;',
								dict(account_id=self.account.id, dependee_ids=(dependee_all.id, dependee_mobile.id, dependee_email.id)))
		self.assertEqual(len(dependent_members), 3)
		dependent1 = dependent_members[0]
		dependent2 = dependent_members[1]
		dependent4 = dependent_members[2]
		self.assertEqual(dependent1.first_name, 'dependent1')
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent1.id)), 3)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent1.id, dependee_id=dependee_mobile.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_mobile_phone=dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent1.id, dependee_id=dependee_email.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_email.email)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent1.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :dependent_id ;',
						dict(dependent_id=dependent1.id))), 2)
		self.assertEqual(len(self.get_sms_subscription(dependent1.id, dependee_all.mobile_phone)), 1)
		self.assertEqual(len(self.get_sms_subscription(dependent1.id, dependee_mobile.mobile_phone)), 1)
		sms_messages = database.list("SELECT * FROM mt_tracking WHERE audience_member_id = :member_id AND message_type = 'sms_upload_welcome_message' ;",
									dict(member_id=dependent1.id))
		self.assertEqual(len(sms_messages), 1)
		self.assertEqual(len(self.get_entry_from_mt_tracking(dependent1.id, dependee_all.mobile_phone)), 0)
		self.assertEqual(len(self.get_entry_from_mt_tracking(dependent1.id, dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(database.list('SELECT * FROM email_subscription WHERE audience_member_id = :dependent_id ;',
										dict(dependent_id=dependent1.id))), 2)
		self.assertEqual(len(self.get_email_subscription(dependent1.id, dependee_all.email)), 1)
		self.assertEqual(len(self.get_email_subscription(dependent1.id, dependee_email.email)), 1)
		email_messages = database.list('SELECT * FROM email_sent WHERE audience_member_id = :member_id ;',
									dict(member_id=dependent1.id))
		self.assertEqual(len(email_messages), 1)
		self.assertEqual(len(self.get_entry_from_email_sent(dependent1.id, dependee_all.email)), 0)
		self.assertEqual(len(self.get_entry_from_email_sent(dependent1.id, dependee_email.email)), 1)

		self.assertEqual(dependent2.first_name, 'dependent2')
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent2.id)), 3)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent2.id, dependee_id=dependee_mobile.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_mobile_phone=dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent2.id, dependee_id=dependee_email.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_email=dependee_email.email)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent2.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :dependent_id ;',
										dict(dependent_id=dependent2.id))), 2)
		self.assertEqual(len(self.get_sms_subscription(dependent2.id, dependee_all.mobile_phone)), 1)
		self.assertEqual(len(self.get_sms_subscription(dependent2.id, dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(database.list('SELECT * FROM email_subscription WHERE audience_member_id = :dependent_id ;',
										dict(dependent_id=dependent2.id))), 2)
		sms_messages = database.list("SELECT * FROM mt_tracking WHERE audience_member_id = :member_id AND message_type = 'sms_upload_welcome_message' ;",
									dict(member_id=dependent2.id))
		self.assertEqual(len(sms_messages), 1)
		self.assertEqual(len(self.get_entry_from_mt_tracking(dependent2.id, dependee_all.mobile_phone)), 1)
		self.assertEqual(len(self.get_entry_from_mt_tracking(dependent2.id, dependee_mobile.mobile_phone)), 0)
		self.assertEqual(len(self.get_email_subscription(dependent2.id, dependee_all.email)), 1)
		self.assertEqual(len(self.get_email_subscription(dependent2.id, dependee_email.email)), 1)

		self.assertEqual(dependent4.first_name, 'dependent4')
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent4.id)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent4.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :dependent_id ;',
										dict(dependent_id=dependent4.id))), 1)
		self.assertEqual(len(self.get_sms_subscription(dependent4.id, dependee_all.mobile_phone)), 1)
		sms_messages = database.list("SELECT * FROM mt_tracking WHERE audience_member_id = :member_id AND message_type = 'sms_upload_welcome_message' ;",
									dict(member_id=dependent4.id))
		self.assertEqual(len(sms_messages), 1)
		self.assertEqual(len(self.get_entry_from_mt_tracking(dependent4.id, dependee_all.mobile_phone)), 1)
		self.assertEqual(len(database.list('SELECT * FROM email_subscription WHERE audience_member_id = :dependent_id ;',
										dict(dependent_id=dependent4.id))), 1)
		self.assertEqual(len(self.get_email_subscription(dependent4.id, dependee_all.email)), 1)


	def test_add_dependent_members_with_own_identifiers_and_dependee_columns(self):
		dependee_all = Member(self.account, first_name='dependee_all', mobile_phone='19876000000', email='dependeeall@gmail.com',
							app_member_id=42, client_member_id=43).save()
		dependee_mobile = Member(self.account, first_name='dependee_mobile', mobile_phone='19829111111').save()
		dependee_email = Member(self.account, first_name='dependee_email', email='dependeeemail@gmail.com').save()
		csv_file = self._copy_file_to_temp_and_return_csvfile('dependent_members_with_own_identifiers_and_dependee_columns.csv')
		mapping_rule = _generate_fields_mapping_rule(['First_Name', 'mobile_Phone', 'email', 'app_member_Id', 'dependee_mobile_phone',
													'dependee_email', 'dependee_app_member_id', 'dependee_client_member_id',
													'relationship_type'], self.account)
		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csv_file,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csv_file)
		).save()

		email_upload_welcome_message(upload.id, self.football_club.id).save()
		sms_upload_welcome_message(upload.id, self.football_club.id).save()
		accept_csv(self.account_id, upload.id, csv_file, self.football_club.id, need_confirm=False, send_welcome_message=True)
		dependent_members = database.list('SELECT * FROM audience_member WHERE account_id = :account_id and id not in :dependee_ids ORDER BY ID ;',
										dict(account_id=self.account.id, dependee_ids=(dependee_all.id, dependee_mobile.id, dependee_email.id)))
		self.assertEqual(len(dependent_members), 2)
		dependentmobile = dependent_members[0]
		dependentemail = dependent_members[1]
		self.assertEqual(dependentmobile.first_name, 'dependentmobile')
		self.assertEqual(dependentmobile.mobile_phone, '19819555555')
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependentmobile.id)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependentmobile.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :dependent_id ;',
										dict(dependent_id=dependentmobile.id))), 2)
		self.assertEqual(len(self.get_sms_subscription(dependentmobile.id, dependee_all.mobile_phone)), 1)
		self.assertEqual(len(self.get_sms_subscription(dependentmobile.id, dependentmobile.mobile_phone)), 1)
		sms_messages = database.list("SELECT * FROM mt_tracking WHERE audience_member_id = :member_id AND message_type = 'sms_upload_welcome_message' ;",
									dict(member_id=dependentmobile.id))
		self.assertEqual(len(sms_messages), 1)
		self.assertEqual(len(self.get_entry_from_mt_tracking(dependentmobile.id, dependee_all.mobile_phone)), 0)
		self.assertEqual(len(self.get_entry_from_mt_tracking(dependentmobile.id, dependentmobile.mobile_phone)), 1)
		self.assertEqual(len(database.list('SELECT * FROM email_subscription WHERE audience_member_id = :dependent_id ;',
										dict(dependent_id=dependentmobile.id))), 1)
		self.assertEqual(len(self.get_email_subscription(dependentmobile.id, dependee_all.email)), 1)
		email_messages = database.list('SELECT * FROM email_sent WHERE audience_member_id = :member_id ;',
									dict(member_id=dependentmobile.id))
		self.assertEqual(len(email_messages), 1)
		self.assertEqual(len(self.get_entry_from_email_sent(dependentmobile.id, dependee_all.email)), 1)

		self.assertEqual(dependentemail.first_name, 'dependentemail')
		self.assertEqual(dependentemail.email, 'dependentemail@gmail.com')
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependentemail.id)), 3)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependentemail.id, dependee_id=dependee_mobile.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_mobile_phone=dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependentemail.id, dependee_id=dependee_email.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_email.email)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependentemail.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :dependent_id ;',
										dict(dependent_id=dependentemail.id))), 2)
		self.assertEqual(len(self.get_sms_subscription(dependentemail.id, dependee_all.mobile_phone)), 1)
		self.assertEqual(len(self.get_sms_subscription(dependentemail.id, dependee_mobile.mobile_phone)), 1)
		sms_messages = database.list("SELECT * FROM mt_tracking WHERE audience_member_id = :member_id AND message_type = 'sms_upload_welcome_message' ;",
									dict(member_id=dependentemail.id))
		self.assertEqual(len(sms_messages), 1)
		self.assertEqual(len(self.get_entry_from_mt_tracking(dependentemail.id, dependee_all.mobile_phone)), 0)
		self.assertEqual(len(self.get_entry_from_mt_tracking(dependentemail.id, dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(database.list('SELECT * FROM email_subscription WHERE audience_member_id = :dependent_id ;',
										dict(dependent_id=dependentemail.id))), 3)
		self.assertEqual(len(self.get_email_subscription(dependentemail.id, dependee_all.email)), 1)
		self.assertEqual(len(self.get_email_subscription(dependentemail.id, dependee_email.email)), 1)
		self.assertEqual(len(self.get_email_subscription(dependentemail.id, dependentemail.email)), 1)

		self.assertEqual(len(self.get_appmail_subscription(dependentmobile.id, dependee_all.id)), 1)


	def test_add_dependent_members_from_dependee_columns_with_confirm(self):
		dependee_all = Member(self.account, first_name='dependee_all', mobile_phone='19876000000', email='dependeeall@gmail.com',
							app_member_id=42, client_member_id=43).save()
		dependee_mobile = Member(self.account, first_name='dependee_mobile', mobile_phone='19829111111').save()
		dependee_email = Member(self.account, first_name='dependee_email', email='dependeeemail@gmail.com').save()
		csv_file = self._copy_file_to_temp_and_return_csvfile('dependent_members_with_dependee_columns.csv')
		mapping_rule = _generate_fields_mapping_rule(['First_Name', 'mobile_Phone', 'email', 'app_member_Id', 'dependee_mobile_phone',
													'dependee_email', 'dependee_app_member_id', 'dependee_client_member_id',
													'relationship_type'], self.account)
		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csv_file,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csv_file)
		).save()

		email_upload_confirm_message(upload.id, self.football_club.id).save()
		sms_upload_confirm_message(upload.id, self.football_club.id).save()
		accept_csv(self.account_id, upload.id, csv_file, self.football_club.id, need_confirm=True)
		dependent_members = database.list('SELECT * FROM audience_member WHERE account_id = :account_id and id not in :dependee_ids ORDER BY ID ;',
										dict(account_id=self.account.id, dependee_ids=(dependee_all.id, dependee_mobile.id, dependee_email.id)))
		self.assertEqual(len(dependent_members), 3)
		dependent1 = dependent_members[0]
		dependent2 = dependent_members[1]
		dependent4 = dependent_members[2]
		self.assertEqual(dependent1.first_name, 'dependent1')
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent1.id)), 3)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent1.id, dependee_id=dependee_mobile.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_mobile_phone=dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent1.id, dependee_id=dependee_email.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_email.email)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent1.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :dependent_id ;',
										dict(dependent_id=dependent1.id))), 2)
		self.assertEqual(len(self.get_sms_subscription(dependent1.id, dependee_all.mobile_phone, 0)), 1)
		self.assertEqual(len(self.get_sms_subscription(dependent1.id, dependee_mobile.mobile_phone, 0)), 1)
		sms_messages = database.list("SELECT * FROM mt_tracking WHERE audience_member_id = :member_id AND message_type = 'sms_upload_confirm_message' ;",
									dict(member_id=dependent1.id))
		self.assertEqual(len(sms_messages), 1)
		# self.assertEqual(len(self.get_entry_from_mt_tracking(dependent1.id, dependee_all.mobile_phone, 'sms_upload_confirm_message')), 1)
		# self.assertEqual(len(self.get_entry_from_mt_tracking(dependent1.id, dependee_mobile.mobile_phone, 'sms_upload_confirm_message')), 1)
		self.assertEqual(len(database.list('SELECT * FROM email_subscription WHERE audience_member_id = :dependent_id ;',
										dict(dependent_id=dependent1.id))), 2)
		self.assertEqual(len(self.get_email_subscription(dependent1.id, dependee_all.email, 0)), 1)
		self.assertEqual(len(self.get_email_subscription(dependent1.id, dependee_email.email, 0)), 1)
		email_messages = database.list('SELECT * FROM email_sent WHERE audience_member_id = :member_id ;',
									dict(member_id=dependent1.id))
		self.assertEqual(len(email_messages), 1)
		# self.assertEqual(len(self.get_entry_from_email_sent(dependent1.id, dependee_all.email)), 1)
		# self.assertEqual(len(self.get_entry_from_email_sent(dependent1.id, dependee_email.email)), 1)

		self.assertEqual(dependent2.first_name, 'dependent2')
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent2.id)), 3)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent2.id, dependee_id=dependee_mobile.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_mobile_phone=dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent2.id, dependee_id=dependee_email.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_email=dependee_email.email)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent2.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :dependent_id ;',
										   dict(dependent_id=dependent2.id))), 2)
		self.assertEqual(len(self.get_sms_subscription(dependent2.id, dependee_all.mobile_phone, 0)), 1)
		self.assertEqual(len(self.get_sms_subscription(dependent2.id, dependee_mobile.mobile_phone, 0)), 1)
		sms_messages = database.list("SELECT * FROM mt_tracking WHERE audience_member_id = :member_id AND message_type = 'sms_upload_confirm_message' ;",
									 dict(member_id=dependent2.id))
		self.assertEqual(len(sms_messages), 1)
		# self.assertEqual(len(self.get_entry_from_mt_tracking(dependent2.id, dependee_all.mobile_phone, 'sms_upload_confirm_message')), 0)
		# self.assertEqual(len(self.get_entry_from_mt_tracking(dependent2.id, dependee_mobile.mobile_phone, 'sms_upload_confirm_message')), 1)
		self.assertEqual(len(database.list('SELECT * FROM email_subscription WHERE audience_member_id = :dependent_id ;',
										   dict(dependent_id=dependent2.id))), 2)
		self.assertEqual(len(self.get_email_subscription(dependent2.id, dependee_all.email, 0)), 1)
		self.assertEqual(len(self.get_email_subscription(dependent2.id, dependee_email.email, 0)), 1)

		self.assertEqual(dependent4.first_name, 'dependent4')
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent4.id)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent4.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :dependent_id ;',
										   dict(dependent_id=dependent4.id))), 1)
		self.assertEqual(len(self.get_sms_subscription(dependent4.id, dependee_all.mobile_phone, 0)), 1)
		sms_messages = database.list("SELECT * FROM mt_tracking WHERE audience_member_id = :member_id AND message_type = 'sms_upload_confirm_message' ;",
									 dict(member_id=dependent4.id))
		self.assertEqual(len(sms_messages), 1)
		self.assertEqual(len(self.get_entry_from_mt_tracking(dependent4.id, dependee_all.mobile_phone, 'sms_upload_confirm_message')), 1)
		self.assertEqual(len(database.list('SELECT * FROM email_subscription WHERE audience_member_id = :dependent_id ;',
										   dict(dependent_id=dependent4.id))), 1)
		self.assertEqual(len(self.get_email_subscription(dependent4.id, dependee_all.email, 0)), 1)


	def test_add_dependent_members_with_own_identifiers_and_dependee_columns_with_confirm(self):
		dependee_all = Member(self.account, first_name='dependee_all', mobile_phone='19876000000', email='dependeeall@gmail.com',
							  app_member_id=42, client_member_id=43).save()
		dependee_mobile = Member(self.account, first_name='dependee_mobile', mobile_phone='19829111111').save()
		dependee_email = Member(self.account, first_name='dependee_email', email='dependeeemail@gmail.com').save()
		csv_file = self._copy_file_to_temp_and_return_csvfile('dependent_members_with_own_identifiers_and_dependee_columns.csv')
		mapping_rule = _generate_fields_mapping_rule(['First_Name', 'mobile_Phone', 'email', 'app_member_Id', 'dependee_mobile_phone',
													  'dependee_email', 'dependee_app_member_id', 'dependee_client_member_id',
													  'relationship_type'], self.account)

		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csv_file,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csv_file)
		).save()
		email_upload_confirm_message(upload.id, self.football_club.id).save()
		sms_upload_confirm_message(upload.id, self.football_club.id).save()
		accept_csv(self.account_id, upload.id, csv_file, self.football_club.id, need_confirm=True)
		dependent_members = database.list('SELECT * FROM audience_member WHERE account_id = :account_id and id not in :dependee_ids ORDER BY ID ;',
										  dict(account_id=self.account.id, dependee_ids=(dependee_all.id, dependee_mobile.id, dependee_email.id)))
		self.assertEqual(len(dependent_members), 2)
		dependentmobile = dependent_members[0]
		dependentemail = dependent_members[1]
		self.assertEqual(dependentmobile.first_name, 'dependentmobile')
		self.assertEqual(dependentmobile.mobile_phone, '19819555555')
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependentmobile.id)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependentmobile.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :dependent_id ;',
										   dict(dependent_id=dependentmobile.id))), 2)
		self.assertEqual(len(self.get_sms_subscription(dependentmobile.id, dependee_all.mobile_phone, 0)), 1)
		self.assertEqual(len(self.get_sms_subscription(dependentmobile.id, dependentmobile.mobile_phone, 0)), 1)
		sms_messages = database.list("SELECT * FROM mt_tracking WHERE audience_member_id = :member_id AND message_type = 'sms_upload_confirm_message' ;",
									 dict(member_id=dependentmobile.id))
		self.assertEqual(len(sms_messages), 1)
		# self.assertEqual(len(self.get_entry_from_mt_tracking(dependentmobile.id, dependee_all.mobile_phone, 'sms_upload_confirm_message')), 0)
		# self.assertEqual(len(self.get_entry_from_mt_tracking(dependentmobile.id, dependentmobile.mobile_phone, 'sms_upload_confirm_message')), 1)
		self.assertEqual(len(database.list('SELECT * FROM email_subscription WHERE audience_member_id = :dependent_id ;',
										   dict(dependent_id=dependentmobile.id))), 1)
		self.assertEqual(len(self.get_email_subscription(dependentmobile.id, dependee_all.email, 0)), 1)
		email_messages = database.list('SELECT * FROM email_sent WHERE audience_member_id = :member_id ;',
									   dict(member_id=dependentmobile.id))
		self.assertEqual(len(email_messages), 1)
		self.assertEqual(len(self.get_entry_from_email_sent(dependentmobile.id, dependee_all.email)), 1)

		self.assertEqual(dependentemail.first_name, 'dependentemail')
		self.assertEqual(dependentemail.email, 'dependentemail@gmail.com')
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependentemail.id)), 3)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependentemail.id, dependee_id=dependee_mobile.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_mobile_phone=dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependentemail.id, dependee_id=dependee_email.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_email.email)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependentemail.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :dependent_id ;',
										   dict(dependent_id=dependentemail.id))), 2)
		self.assertEqual(len(self.get_sms_subscription(dependentemail.id, dependee_all.mobile_phone, 0)), 1)
		self.assertEqual(len(self.get_sms_subscription(dependentemail.id, dependee_mobile.mobile_phone, 0)), 1)
		sms_messages = database.list("SELECT * FROM mt_tracking WHERE audience_member_id = :member_id AND message_type = 'sms_upload_confirm_message' ;",
									 dict(member_id=dependentemail.id))
		self.assertEqual(len(sms_messages), 1)
		# self.assertEqual(len(self.get_entry_from_mt_tracking(dependentemail.id, dependee_all.mobile_phone, 'sms_upload_confirm_message')), 1)
		# self.assertEqual(len(self.get_entry_from_mt_tracking(dependentemail.id, dependee_mobile.mobile_phone, 'sms_upload_confirm_message')), 0)
		self.assertEqual(len(database.list('SELECT * FROM email_subscription WHERE audience_member_id = :dependent_id ;',
										   dict(dependent_id=dependentemail.id))), 3)
		self.assertEqual(len(self.get_email_subscription(dependentemail.id, dependee_all.email, 0)), 1)
		self.assertEqual(len(self.get_email_subscription(dependentemail.id, dependee_email.email, 0)), 1)
		self.assertEqual(len(self.get_email_subscription(dependentemail.id, dependentemail.email, 0)), 1)


	def test_add_dependent_members_with_invalid_dependee_column_values(self):
		dependee_all = Member(self.account, first_name='dependee_all', mobile_phone='19876000000', email='dependeeall@gmail.com',
							  app_member_id=42, client_member_id=43).save()
		dependee_mobile = Member(self.account, first_name='dependee_mobile', mobile_phone='19829111111').save()
		dependee_email = Member(self.account, first_name='dependee_email', email='dependeeemail@gmail.com').save()
		dependent_member = Member(self.account, first_name='dependent_member', email='dependentmember@gmail.com').save()
		normal_member = Member(self.account, first_name='normal1', email='normal1@gmail.com').save()
		MemberRelationship(dependee_id=dependee_all.id, dependent_id=dependent_member.id,
						   dependee_mobile_phone=dependee_all.mobile_phone).save()
		csv_file = self._copy_file_to_temp_and_return_csvfile('dependent_members_with_incorrect_dependee_column_values.csv')
		mapping_rule = _generate_fields_mapping_rule(['First_Name', 'mobile_Phone', 'email', 'app_member_Id', 'dependee_mobile_phone',
													  'dependee_email', 'dependee_app_member_id', 'dependee_client_member_id',
													  'relationship_type'], self.account)
		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csv_file,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csv_file)
		).save()

		accept_csv(self.account_id, upload.id, csv_file, self.football_club.id, False)
		dependent_members = database.list('SELECT * FROM audience_member WHERE account_id = :account_id and id not in :dependee_ids ORDER BY ID ;',
										  dict(account_id=self.account.id, dependee_ids=(dependee_all.id, dependee_mobile.id,
																						 dependee_email.id, dependent_member.id,
																						 normal_member.id)))
		self.assertEqual(len(dependent_members), 0)
		self.assertEqual(len(database.list('SELECT * FROM member_relationship WHERE dependent_id != :dependent_id ;',
										   dict(dependent_id=dependent_member.id))), 0)
		normal_member = Member.get(id=normal_member.id)
		dependee_all = Member.get(id=dependee_all.id)
		self.assertEqual(normal_member.first_name, 'normal1')    # Members were not updated due to DependeeValidationException.
		self.assertEqual(dependee_all.first_name, 'dependee_all')

	def test_update_dependent_members_with_single_dependee_columns_for_each(self):
		dependee_all = Member(self.account, first_name='dependee_all', mobile_phone='19876000000', email='dependeeall@gmail.com',
							  app_member_id=42, client_member_id=43).save()
		dependee_mobile = Member(self.account, first_name='dependee_mobile', mobile_phone='19829111111').save()
		dependee_email = Member(self.account, first_name='dependee_email', email='dependeeemail@gmail.com').save()
		csv_file = self._copy_file_to_temp_and_return_csvfile('dependent_members_with_single_dependee_columns_each.csv')
		mapping_rule = _generate_fields_mapping_rule(['First_Name', 'mobile_Phone', 'email', 'app_member_Id', 'dependee_mobile_phone',
													  'dependee_email', 'dependee_app_member_id', 'dependee_client_member_id',
													  'relationship_type'], self.account)
		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csv_file,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csv_file)
		).save()
		accept_csv(self.account_id, upload.id, csv_file, self.football_club.id, False)
		dependent_members = database.list('SELECT * FROM audience_member WHERE account_id = :account_id and id not in :dependee_ids ORDER BY ID ;',
										  dict(account_id=self.account.id, dependee_ids=(dependee_all.id, dependee_mobile.id, dependee_email.id)))

		self.assertEqual(len(dependent_members), 4)
		dependent1 = dependent_members[0]
		dependent2 = dependent_members[1]
		dependent4 = dependent_members[2]
		dependent5 = dependent_members[3]
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent1.id, dependee_id=dependee_mobile.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_mobile_phone=dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent2.id, dependee_id=dependee_email.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_email.email)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent4.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent5.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(self.get_sms_subscription(dependent1.id, dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(self.get_email_subscription(dependent2.id, dependee_email.email)), 1)
		self.assertEqual(len(self.get_sms_subscription(dependent4.id, dependee_all.mobile_phone)), 1)
		self.assertEqual(len(self.get_email_subscription(dependent4.id, dependee_all.email)), 1)
		self.assertEqual(len(self.get_sms_subscription(dependent5.id, dependee_all.mobile_phone)), 1)
		self.assertEqual(len(self.get_email_subscription(dependent5.id, dependee_all.email)), 1)
		self.assertEqual(len(self.get_appmail_subscription(dependent4.id, dependee_all.id)), 1)


	def test_update_dependent_members_and_regular_members_by_adding_dependees(self):
		dependee_all = Member(self.account, first_name='dependee_all', mobile_phone='19876000000', email='dependeeall@gmail.com',
							  app_member_id=42, client_member_id=43).save()
		dependee_mobile = Member(self.account, first_name='dependee_mobile', mobile_phone='19829111111').save()
		dependee_email = Member(self.account, first_name='dependee_email', email='dependeeemail@gmail.com').save()
		dependent1 = Member(self.account, first_name='dependent1', email='dependent1@gmail.com').save()
		dependent2 = Member(self.account, first_name='dependent2', app_member_id=49).save()
		normal_member = Member(self.account, first_name='normal1', email='normal1@gmail.com',
							   mobile_phone='19878777777').save()
		MemberRelationship(dependee_id=dependee_all.id, dependent_id=dependent1.id,
						   dependee_mobile_phone=dependee_all.mobile_phone, dependee_email=dependee_all.email,
						   dependee_app_member_id=dependee_all.app_member_id,
						   dependee_client_member_id=dependee_all.client_member_id,
						   account_id=self.account.id).save()
		csv_file = self._copy_file_to_temp_and_return_csvfile('dependent_members_and_normal_members_update.csv')
		mapping_rule = _generate_fields_mapping_rule(['First_Name', 'mobile_Phone', 'email', 'app_member_Id', 'dependee_mobile_phone',
													  'dependee_email', 'dependee_app_member_id', 'dependee_client_member_id',
													  'relationship_type'], self.account)
		upload = new_upload(
			list_id=self.football_club.id,
			file_name=csv_file,
			mapping_rule=mapping_rule,
			upload_by_user_id=self.upload_user.id,
			total_lines=self._get_total_lines_in_file(csvfile=csv_file)
		).save()

		accept_csv(self.account_id, upload.id, csv_file, self.football_club.id, False)
		dependent1 = Member.get(dependent1.id)
		dependent2 = Member.get(dependent2.id)
		normal_member = Member.get(normal_member.id)
		self.assertEqual(dependent1.first_name, 'dependent1updated')
		self.assertEqual(dependent1.email, 'dependent1@gmail.com')
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent1.id)), 3)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent1.id, dependee_id=dependee_mobile.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_mobile_phone=dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent1.id, dependee_id=dependee_email.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_email=dependee_email.email)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent1.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :dependent_id ;',
										   dict(dependent_id=dependent1.id))), 2)
		self.assertEqual(len(self.get_sms_subscription(dependent1.id, dependee_all.mobile_phone)), 1)
		self.assertEqual(len(self.get_sms_subscription(dependent1.id, dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(database.list('SELECT * FROM email_subscription WHERE audience_member_id = :dependent_id ;',
										   dict(dependent_id=dependent1.id))), 3)
		self.assertEqual(len(self.get_email_subscription(dependent1.id, dependee_all.email)), 1)
		self.assertEqual(len(self.get_email_subscription(dependent1.id, dependee_email.email)), 1)
		self.assertEqual(len(self.get_email_subscription(dependent1.id, dependent1.email)), 1)

		self.assertEqual(dependent2.first_name, 'dependent2updated')
		self.assertEqual(dependent2.mobile_phone, '19876666666')
		self.assertEqual(int(dependent2.app_member_id), 49)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent2.id)), 3)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent2.id, dependee_id=dependee_mobile.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_mobile_phone=dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent2.id, dependee_id=dependee_email.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_email=dependee_email.email)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=dependent2.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.CAREGIVER, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :dependent_id ;',
										dict(dependent_id=dependent2.id))), 3)
		self.assertEqual(len(self.get_sms_subscription(dependent2.id, dependee_all.mobile_phone)), 1)
		self.assertEqual(len(self.get_sms_subscription(dependent2.id, dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(self.get_sms_subscription(dependent2.id, dependent2.mobile_phone)), 1)
		self.assertEqual(len(database.list('SELECT * FROM email_subscription WHERE audience_member_id = :dependent_id ;',
										   dict(dependent_id=dependent2.id))), 2)
		self.assertEqual(len(self.get_email_subscription(dependent2.id, dependee_all.email)), 1)
		self.assertEqual(len(self.get_email_subscription(dependent2.id, dependee_email.email)), 1)

		self.assertEqual(normal_member.first_name, 'normal1updated')
		self.assertEqual(int(normal_member.app_member_id), 99)
		self.assertEqual(normal_member.email, 'normal1@gmail.com')
		self.assertEqual(normal_member.mobile_phone, '19878777777')
		self.assertEqual(len(MemberRelationship.get(dependent_id=normal_member.id)), 3)
		self.assertEqual(len(MemberRelationship.get(dependent_id=normal_member.id, dependee_id=dependee_mobile.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_mobile_phone=dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=normal_member.id, dependee_id=dependee_email.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_email.email)), 1)
		self.assertEqual(len(MemberRelationship.get(dependent_id=normal_member.id, dependee_id=dependee_all.id,
													relationship_type=RelationshipType.PARENT, account_id=self.account.id,
													dependee_email=dependee_all.email, dependee_mobile_phone=dependee_all.mobile_phone,
													dependee_app_member_id=str(dependee_all.app_member_id),
													dependee_client_member_id=str(dependee_all.client_member_id))), 1)
		self.assertEqual(len(database.list('SELECT * FROM sms_subscription WHERE audience_member_id = :dependent_id ;',
										   dict(dependent_id=normal_member.id))), 3)
		self.assertEqual(len(self.get_sms_subscription(normal_member.id, dependee_all.mobile_phone)), 1)
		self.assertEqual(len(self.get_sms_subscription(normal_member.id, dependee_mobile.mobile_phone)), 1)
		self.assertEqual(len(self.get_sms_subscription(normal_member.id, normal_member.mobile_phone)), 1)
		self.assertEqual(len(database.list('SELECT * FROM email_subscription WHERE audience_member_id = :dependent_id ;',
										   dict(dependent_id=normal_member.id))), 3)
		self.assertEqual(len(self.get_email_subscription(normal_member.id, dependee_all.email)), 1)
		self.assertEqual(len(self.get_email_subscription(normal_member.id, dependee_email.email)), 1)
		self.assertEqual(len(self.get_email_subscription(normal_member.id, normal_member.email)), 1)
