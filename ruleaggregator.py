from conditionanalyser import ConditionAnalyser

class RuleAggregator:
    """
    Aggregates rules for a specific disease category.
    """

    def __init__(self, category, disease_name, disease_code, rules, _id=None, rule_id=None, conditions=None):
        """
        Initializes the RuleAggregator with the given parameters.
        
        :param category: Category of the disease.
        :param disease_name: Name of the disease.
        :param disease_code: Code of the disease.
        :param rules: List of RuleEntry objects.
        :param _id: MongoDB ObjectId (optional).
        :param rule_id: ID of the rule (optional).
        :param conditions: List of conditions (optional).
        """
        self.category = category
        self.disease_name = disease_name
        self.disease_code = disease_code
        self.rules = rules
        self._id = _id
        self.rule_id = rule_id
        self.conditions = conditions if conditions is not None else []

    def RuleEntry(self, rule_id, conditions):
        """
        Method to add a new rule entry to the aggregator.
        
        :param rule_id: ID of the rule.
        :param conditions: Conditions associated with the rule.
        """
        self.rule_id = rule_id
        self.conditions = conditions

    def to_dict(self):
        """
        Convert the RuleAggregator instance to a dictionary.
        
        :return: Dictionary representation of the instance.
        """
        return {
            'category': self.category,
            'disease_name': self.disease_name,
            'disease_code': self.disease_code,
            'rules': [rule.to_dict() for rule in self.rules],
            '_id': self._id,
            'rule_id': self.rule_id,
            'conditions': [condition.to_dict() for condition in self.conditions]
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a RuleAggregator instance from a dictionary.
        
        :param data: Dictionary containing the necessary data.
        :return: RuleAggregator instance.
        """
        rules = [RuleEntry.from_dict(rule_entry) for rule_entry in data.get('rules', [])]
        conditions = [ConditionAnalyser.from_dict(condition) for condition in data.get('conditions', [])]
        return cls(
            category=data.get('category'),
            disease_name=data.get('disease_name'),
            disease_code=data.get('disease_code'),
            rules=rules,
            _id=data.get('_id'),
            rule_id=data.get('rule_id'),
            conditions=conditions
        )

class RuleEntry:
    """
    Represents a single rule entry with an ID and associated conditions.
    """

    def __init__(self, rule_id, conditions):
        """
        Initializes the RuleEntry with the given parameters.
        
        :param rule_id: ID of the rule.
        :param conditions: Conditions associated with the rule.
        """
        self.rule_id = rule_id
        self.conditions = conditions

    def to_dict(self):
        """
        Convert the RuleEntry instance to a dictionary.
        
        :return: Dictionary representation of the instance.
        """
        return {
            'rule_id': self.rule_id,
            'conditions': [condition.to_dict() for condition in self.conditions]
        }

    @staticmethod
    def from_dict(rule_entry_data):
        """
        Create a RuleEntry instance from a dictionary.
        
        :param rule_entry_data: Dictionary containing the necessary data.
        :return: RuleEntry instance.
        """
        conditions = [ConditionAnalyser.from_dict(condition) for condition in rule_entry_data.get('conditions', [])]
        return RuleEntry(
            rule_entry_data.get('rule_id'),
            conditions
        )