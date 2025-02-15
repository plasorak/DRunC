from drunc.utils.configuration import ConfHandler



class KafkaBroadcastSenderConfData:
    def __init__(self, address=None, publish_timeout=None):
        self.address = address
        self.publish_timeout = publish_timeout

    @staticmethod
    def from_dict(data:dict):
        address = data.get('address')
        if address is None:
            address = data['kafka_address']

        return KafkaBroadcastSenderConfData(
            address = address,
            publish_timeout = data['publish_timeout']
        )

class BroadcastSenderConfHandler(ConfHandler):
    def _post_process_oks(self):
        from drunc.broadcast.types import BroadcastTypes
        self.impl_technology = BroadcastTypes.Kafka if self.data else None
        self.log.debug(self.data)

    def get_impl_technology(self):
        return self.impl_technology

    def _parse_dict(self, data):
        if data == {}:
            self.impl_technology = None
            return None
        return KafkaBroadcastSenderConfData.from_dict(data)