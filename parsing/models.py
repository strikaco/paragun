from common.models import AbstractBaseModel
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction

import logging
import re
import timeit

class Service(AbstractBaseModel):
    
    class Meta:
        unique_together = ('token', 'key')
    
    token = models.ForeignKey('common.Token', blank=True, null=True, on_delete=models.CASCADE)
    key = models.CharField(max_length=8)
    
    def __str__(self):
        if self.token:
            return '%s (%s)' % (self.key, self.token)
        else:
            return '%s' % self.key
            
    def get_parsers(self, *args, **kwargs):
        return self.parsers.enabled()
        
    @classmethod
    def get_parser_map(cls, *args, **kwargs):
        """
        Return a dictionary mapping of all service names and their defined
        parsers, sorted by priority.
        
        Parsers that are disabled or in untested/failure states are excluded.
        
        Returns:
            mapping (dict): {
                service: {
                    fieldname: [validator, [parsers]],
                    fieldname2: [validator, [parsers]],
                }
            }
        
        """
        services = cls.objects.enabled()
        
        return {
            service.key: {
                parser.field.key: {
                    'validator': parser.field.validator,
                    'parsers': list(service.parsers.enabled().filter(field=parser.field).order_by('priority').values_list('value', flat=True))
                } for parser in service.parsers.enabled()
            } for service in services
        }
        
    def test(self, *args, **kwargs):
        # Get all valid log samples for this service
        samples = self.samples.enabled()
        
        with transaction.atomic():
            for sample in samples:
                sample.status = True
                
                for assertion in sample.assertions.enabled():
                    # Get parsers for this field for this service
                    parsers = self.parsers.enabled().filter(field=assertion.key)
                    
                    # Run each against sample until a valid value is found
                    value = None
                    for parser in parsers:
                        value = parser.parse(sample.value)
                        if value: break
                    
                    try:
                        assert value == assertion.value
                        assertion.status = True
                    except AssertionError:
                        assertion.status = False
                    
                    assertion.save()
                    
                    if assertion.status == False:
                        sample.status = False
                    
                sample.save()
                
        if self.samples.enabled().filter(status=False).exists():
            return False
        return True
                
                
class Parser(AbstractBaseModel):
    
    class Meta:
        ordering = ('field', 'priority')
    
    enabled = models.BooleanField(default=False, help_text="Whether or not this object should be enabled.")
    service = models.ForeignKey('parsing.Service', on_delete=models.CASCADE, related_name='parsers')
    
    priority = models.PositiveSmallIntegerField(default=50)
    field = models.ForeignKey('parsing.Field', on_delete=models.CASCADE)
    value = models.TextField()
    
    @property
    def regex(self):
        if not getattr(self, '_compiled', None):
            self._compiled = re.compile(self.value)
        return self._compiled
    
    def __str__(self):
        return '%s: %s (%s)' % (self.service.key, self.field.key, self.priority)
        
    def parse(self, string, *args, **kwargs):
        try: return self.regex.search(string).group(1)
        except: return ''
    
    def save(self, *args, **kwargs):
        # Validate regex, make sure there are no obvious syntax errors
        obj = self.regex
        
        # TODO: disallow stupid match-all regexes and other performance-killers
        
        # TODO: validate regex performance; should meet certain threshold
        
        super().save(*args, **kwargs)


class Sample(AbstractBaseModel):
    
    class Meta:
        ordering = ('-created',)
    
    service = models.ForeignKey('parsing.Service', on_delete=models.CASCADE, related_name='samples')
    status = models.BooleanField(default=False)
    value = models.TextField()
    
    
class Assertion(AbstractBaseModel):
    
    class Meta:
        unique_together = ('sample', 'key')
    
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='assertions')
    status = models.BooleanField(default=False)
    key = models.ForeignKey('parsing.Field', on_delete=models.CASCADE)
    value = models.CharField(max_length=64)
    
    def __str__(self):
        return '%s: %s' % (str(self.key), self.value)
        
    
class Field(AbstractBaseModel):
    
    class Meta:
        ordering = ('key',)
    
    key = models.CharField(max_length=32, unique=True)
    description = models.TextField(blank=True, null=True)
    validator = models.TextField(default="(.*)", help_text="Regex string to apply against parsed value to detect match. Use '(.*)' to match any.")
    
    def __str__(self):
        return self.key
        
    def save(self, *args, **kwargs):
        # Check validator for syntax errors
        re.compile(self.validator)
        
        super().save(*args, **kwargs)
        
try:
    logger = logging.getLogger(__name__)
    logger.info("Populating database with default fields...")
    default_fields = ['action', 'additional_answer_count', 'affect_dest', 'answer', 'answer_count', 'app', 'array', 'authority_answer_count', 'availability', 'avg_executions', 'blocksize', 'body', 'buffer_cache_hit_ratio', 'bugtraq', 'bytes', 'bytes_in', 'bytes_out', 'cached', 'category', 'cert', 'change', 'change_type', 'channel', 'cluster', 'cm_enabled', 'cm_supported', 'command', 'comments', 'commits', 'committed_memory', 'compilation_time', 'cookie', 'cpu_cores', 'cpu_count', 'cpu_load_mhz', 'cpu_load_percent', 'cpu_mhz', 'cpu_time', 'cpu_time_enabled', 'cpu_time_supported', 'cpu_used', 'current_cpu_time', 'current_loaded', 'current_user_time', 'cursor', 'cve', 'cvss', 'daemon_thread_count', 'date', 'delay', 'description', 'dest', 'dest_bunit', 'dest_category', 'dest_dns', 'dest_interface', 'dest_ip', 'dest_mac', 'dest_nt_domain', 'dest_nt_host', 'dest_port', 'dest_priority', 'dest_requires_av', 'dest_should_timesync', 'dest_should_update', 'dest_translated_ip', 'dest_translated_port', 'dest_zone', 'direction', 'dlp_type', 'dns', 'dump_area_used', 'duration', 'dvc', 'dvc_bunit', 'dvc_category', 'dvc_ip', 'dvc_mac', 'dvc_priority', 'dvc_zone', 'elapsed_time', 'enabled', 'endpoint', 'endpoint_version', 'family', 'fd_max', 'file_access_time', 'file_acl', 'file_create_time', 'file_hash', 'file_modify_time', 'file_name', 'file_path', 'file_size', 'filter_action', 'filter_score', 'flow_id', 'free_bytes', 'free_physical_memory', 'free_swap', 'heap_committed', 'heap_initial', 'heap_max', 'heap_used', 'http_content_type', 'http_method', 'http_referrer', 'http_user_agent', 'http_user_agent_length', 'hypervisor', 'hypervisor_id', 'icmp_code', 'icmp_type', 'id', 'ids_type', 'incident', 'indexes_hit', 'inline_nat', 'instance_name', 'instance_reads', 'instance_version', 'instance_writes', 'interactive', 'interface', 'internal_message_id', 'ip', 'jvm_description', 'last_call_minute', 'latency', 'lb_method', 'lease_duration', 'lease_scope', 'lock_mode', 'lock_session_id', 'logical_reads', 'logon_time', 'mac', 'machine', 'max_file_descriptors', 'mem', 'mem_used', 'memory_sorts', 'message', 'message_consumed_time', 'message_correlation_id', 'message_delivered_time', 'message_delivery_mode', 'message_expiration_time', 'message_id', 'message_info', 'message_priority', 'message_properties', 'message_received_time', 'message_redelivered', 'message_reply_dest', 'message_type', 'mount', 'msft', 'mskb', 'name', 'node', 'node_port', 'non_heap_committed', 'non_heap_initial', 'non_heap_max', 'non_heap_used', 'number_of_users', 'obj_name', 'object', 'object_attrs', 'object_category', 'object_id', 'object_path', 'objects_pending', 'omu_supported', 'open_file_descriptors', 'orig_dest', 'orig_recipient', 'orig_src', 'os', 'os_architecture', 'os_pid', 'os_version', 'packets', 'packets_in', 'packets_out', 'parameters', 'parent', 'password', 'payload', 'payload_type', 'peak_thread_count', 'physical_memory', 'physical_reads', 'priority', 'problem', 'process', 'process_id', 'process_limit', 'process_name', 'processes', 'product_version', 'protocol', 'protocol_version', 'query', 'query_count', 'query_id', 'query_plan_hit', 'query_time', 'query_type', 'read_blocks', 'read_latency', 'read_ops', 'recipient', 'recipient_count', 'recipient_status', 'record_type', 'records_affected', 'reply_code', 'reply_code_id', 'request_payload', 'request_payload_type', 'request_sent_time', 'response_code', 'response_payload_type', 'response_received_time', 'response_time', 'result', 'result_id', 'retries', 'return_addr', 'return_message', 'rpc_protocol', 'rule', 'seconds_in_wait', 'sender', 'serial', 'serial_num', 'service', 'service_id', 'session_id', 'session_limit', 'session_status', 'sessions', 'severity', 'severity_id', 'sga_buffer_cache_size', 'sga_buffer_hit_limit', 'sga_data_dict_hit_ratio', 'sga_fixed_area_size', 'sga_free_memory', 'sga_library_cache_size', 'sga_redo_log_buffer_size', 'sga_shared_pool_size', 'sga_sql_area_size', 'shell', 'signature', 'signature_extra', 'signature_id', 'signature_version', 'site', 'size', 'snapshot', 'src', 'src_bunit', 'src_category', 'src_dns', 'src_interface', 'src_ip', 'src_mac', 'src_nt_domain', 'src_nt_host', 'src_port', 'src_priority', 'src_translated_ip', 'src_translated_port', 'src_user', 'src_user_bunit', 'src_user_category', 'src_user_priority', 'src_zone', 'ssid', 'ssl_end_time', 'ssl_engine', 'ssl_hash', 'ssl_is_valid', 'ssl_issuer', 'ssl_issuer_common_name', 'ssl_issuer_email', 'ssl_issuer_locality', 'ssl_issuer_organization', 'ssl_issuer_state', 'ssl_issuer_street', 'ssl_issuer_unit', 'ssl_name', 'ssl_policies', 'ssl_publickey', 'ssl_publickey_algorithm', 'ssl_serial', 'ssl_session_id', 'ssl_signature_algorithm', 'ssl_start_time', 'ssl_subject', 'ssl_subject_common_name', 'ssl_subject_email', 'ssl_subject_locality', 'ssl_subject_organization', 'ssl_subject_state', 'ssl_subject_street', 'ssl_subject_unit', 'ssl_validity_window', 'ssl_version', 'start_mode', 'start_time', 'status', 'status_code', 'storage', 'stored_procedures_called', 'subject', 'swap_space', 'synch_supported', 'system_load', 'table_scans', 'tables_hit', 'tablespace_name', 'tablespace_reads', 'tablespace_status', 'tablespace_used', 'tablespace_writes', 'tag', 'tcp_flag', 'thread_count', 'threads_started', 'ticket_id', 'time', 'time_submitted', 'tos', 'total_loaded', 'total_processors', 'total_unloaded', 'transaction_id', 'transport', 'transport_dest_port', 'ttl', 'type', 'uptime', 'uri_path', 'uri_query', 'url', 'url_length', 'user', 'user_bunit', 'user_category', 'user_id', 'user_priority', 'vendor_product', 'version', 'vip_port', 'vlan', 'wait_state', 'wait_time', 'wifi', 'write_blocks', 'write_latency', 'write_ops', 'xdelay', 'xref']
    
    for field in default_fields:
        Field.objects.create(key=field)
        
except Exception as e:
    logger.warn("Failed to populate default fields.")
    logger.warn(e)