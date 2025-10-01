"""
Automatic Database Creator for Payment Scripts and Card Approval Management.
Creates structured JSON databases with separate folders for approved/not-approved cards.
Converts payment data to script format for easy execution and management.
"""
import json
import hashlib
import sqlite3
import datetime
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import uuid

from ..utils.logger import Logger

logger = Logger("DatabaseCreator")


@dataclass
class PaymentScript:
    """Payment script data structure with execution details."""
    script_id: str
    card_hash: str
    card_brand: str
    card_type: str
    pan_masked: str
    issuer_country: str
    currency_code: str
    terminal_type: str
    bypass_method: str
    tlv_modifications: List[Dict[str, str]]
    execution_commands: List[str]
    success_rate: float
    success_count: int
    failure_count: int
    confidence_level: str
    risk_score: float
    geographic_region: str
    approval_status: str
    created_date: str
    last_updated: str
    execution_time_ms: int
    notes: str
    tags: List[str]


@dataclass
class ScriptExecution:
    """Script execution result data structure."""
    execution_id: str
    script_id: str
    timestamp: str
    result: str  # 'success', 'failure', 'error'
    execution_time_ms: int
    terminal_response: str
    error_details: Optional[str]
    operator_notes: str


class AutomaticDatabaseCreator:
    """Automatic database creator for payment scripts and card approval management."""
    
    def __init__(self, base_path: str = "databases"):
        """Initialize the automatic database creator."""
        self.base_path = Path(base_path)
        self.approved_path = self.base_path / "approved"
        self.not_approved_path = self.base_path / "not_approved"
        self.scripts_path = self.base_path / "scripts"
        
        # Create directory structure
        for path in [self.approved_path, self.not_approved_path, self.scripts_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Initialize counters
        self.approved_count = 0
        self.not_approved_count = 0
        self.script_count = 0
        
        logger.info(f"Database creator initialized with base path: {self.base_path}")
    
    def convert_payment_to_script(self, payment_data: Dict[str, Any]) -> PaymentScript:
        """
        Convert payment database entry to executable script format.
        
        Args:
            payment_data: Payment data from database
            
        Returns:
            PaymentScript object ready for execution
        """
        try:
            # Generate unique script ID
            script_id = f"SCRIPT_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
            
            # Extract card information
            card_hash = payment_data.get('card_hash', '')
            card_brand = payment_data.get('card_brand', 'Unknown')
            card_type = payment_data.get('card_type', 'Credit Card')
            
            # Mask PAN for security
            pan = payment_data.get('pan', '')
            pan_masked = self._mask_pan(pan) if pan else 'XXXX-XXXX-XXXX-XXXX'
            
            # Geographic and currency information
            issuer_country = payment_data.get('issuer_country', 'Unknown')
            currency_code = payment_data.get('currency_code', 'XXX')
            geographic_region = self._get_geographic_region(issuer_country)
            
            # Payment method details
            terminal_type = payment_data.get('terminal_type', 'POS')
            bypass_method = payment_data.get('bypass_method', 'signature')
            
            # TLV modifications
            tlv_mods = payment_data.get('tlv_modifications', [])
            if isinstance(tlv_mods, str):
                try:
                    tlv_mods = json.loads(tlv_mods)
                except:
                    tlv_mods = []
            
            # Success metrics
            success_count = payment_data.get('success_count', 0)
            failure_count = payment_data.get('failure_count', 0)
            total_attempts = success_count + failure_count
            success_rate = success_count / total_attempts if total_attempts > 0 else 0.0
            
            # Determine confidence and approval status
            confidence_level = self._calculate_confidence(success_rate, success_count)
            approval_status = self._determine_approval_status(success_rate, success_count, failure_count)
            risk_score = self._calculate_risk_score(payment_data)
            
            # Generate execution commands
            execution_commands = self._generate_execution_commands(
                bypass_method, tlv_mods, terminal_type, card_brand
            )
            
            # Calculate estimated execution time
            execution_time_ms = self._estimate_execution_time(bypass_method, len(tlv_mods))
            
            # Generate tags for categorization
            tags = self._generate_tags(card_brand, card_type, bypass_method, approval_status, geographic_region)
            
            # Create payment script
            script = PaymentScript(
                script_id=script_id,
                card_hash=card_hash,
                card_brand=card_brand,
                card_type=card_type,
                pan_masked=pan_masked,
                issuer_country=issuer_country,
                currency_code=currency_code,
                terminal_type=terminal_type,
                bypass_method=bypass_method,
                tlv_modifications=tlv_mods,
                execution_commands=execution_commands,
                success_rate=success_rate,
                success_count=success_count,
                failure_count=failure_count,
                confidence_level=confidence_level,
                risk_score=risk_score,
                geographic_region=geographic_region,
                approval_status=approval_status,
                created_date=datetime.datetime.now().isoformat(),
                last_updated=datetime.datetime.now().isoformat(),
                execution_time_ms=execution_time_ms,
                notes=payment_data.get('notes', ''),
                tags=tags
            )
            
            logger.debug(f"Converted payment to script: {script_id} ({approval_status})")
            return script
            
        except Exception as e:
            logger.error(f"Failed to convert payment to script: {e}")
            raise
    
    def save_script_to_database(self, script: PaymentScript) -> bool:
        """
        Save payment script to appropriate database folder based on approval status.
        
        Args:
            script: PaymentScript to save
            
        Returns:
            True if saved successfully
        """
        try:
            # Determine target folder based on approval status
            if script.approval_status == 'approved':
                target_folder = self.approved_path
                self.approved_count += 1
            else:
                target_folder = self.not_approved_path
                self.not_approved_count += 1
            
            # Create filename with metadata
            filename = f"{script.script_id}_{script.card_brand}_{script.bypass_method}.json"
            filepath = target_folder / filename
            
            # Prepare script data for JSON export
            script_data = {
                "metadata": {
                    "script_id": script.script_id,
                    "approval_status": script.approval_status,
                    "confidence_level": script.confidence_level,
                    "success_rate": script.success_rate,
                    "risk_score": script.risk_score,
                    "created_date": script.created_date,
                    "last_updated": script.last_updated,
                    "tags": script.tags
                },
                "card_information": {
                    "card_hash": script.card_hash,
                    "card_brand": script.card_brand,
                    "card_type": script.card_type,
                    "pan_masked": script.pan_masked,
                    "issuer_country": script.issuer_country,
                    "currency_code": script.currency_code,
                    "geographic_region": script.geographic_region
                },
                "payment_method": {
                    "terminal_type": script.terminal_type,
                    "bypass_method": script.bypass_method,
                    "tlv_modifications": script.tlv_modifications,
                    "execution_time_ms": script.execution_time_ms
                },
                "execution_script": {
                    "commands": script.execution_commands,
                    "prerequisites": self._generate_prerequisites(script),
                    "validation_steps": self._generate_validation_steps(script),
                    "rollback_commands": self._generate_rollback_commands(script)
                },
                "performance_metrics": {
                    "success_count": script.success_count,
                    "failure_count": script.failure_count,
                    "success_rate": script.success_rate,
                    "confidence_level": script.confidence_level,
                    "risk_score": script.risk_score
                },
                "notes_and_comments": {
                    "operator_notes": script.notes,
                    "warnings": self._generate_warnings(script),
                    "recommendations": self._generate_recommendations(script)
                }
            }
            
            # Save to JSON file with pretty formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
            
            # Also save to scripts folder for quick access
            script_filepath = self.scripts_path / f"{script.script_id}.json"
            with open(script_filepath, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
            
            self.script_count += 1
            logger.info(f"Saved script {script.script_id} to {target_folder.name} database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save script {script.script_id}: {e}")
            return False
    
    def create_databases_from_sqlite(self, sqlite_path: str) -> Dict[str, int]:
        """
        Create JSON databases from existing SQLite payment database.
        
        Args:
            sqlite_path: Path to SQLite database
            
        Returns:
            Statistics of created databases
        """
        try:
            logger.info(f"Creating databases from SQLite: {sqlite_path}")
            
            # Connect to SQLite database
            with sqlite3.connect(sqlite_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable column access by name
                
                # Get all payment records
                cursor = conn.execute("""
                    SELECT ap.*, cp.bin_range, cp.issuer_country, cp.risk_level, cp.profile_data
                    FROM approved_payments ap
                    LEFT JOIN card_profiles cp ON ap.card_hash = cp.card_hash
                    ORDER BY ap.success_rate DESC, ap.success_count DESC
                """)
                
                payment_records = cursor.fetchall()
                
                # Convert each payment to script and save
                for record in payment_records:
                    # Convert row to dictionary
                    payment_data = dict(record)
                    
                    # Convert to script format
                    script = self.convert_payment_to_script(payment_data)
                    
                    # Save to appropriate database
                    self.save_script_to_database(script)
            
            # Create summary report
            summary = self._create_database_summary()
            
            logger.info(f"Database creation complete: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to create databases from SQLite: {e}")
            return {"error": str(e)}
    
    def create_execution_report(self, script_id: str, result: ScriptExecution) -> bool:
        """
        Create execution report for a script.
        
        Args:
            script_id: Script identifier
            result: Execution result
            
        Returns:
            True if report created successfully
        """
        try:
            # Create execution reports folder
            reports_path = self.base_path / "execution_reports"
            reports_path.mkdir(exist_ok=True)
            
            # Create report filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f"execution_{script_id}_{timestamp}.json"
            report_filepath = reports_path / report_filename
            
            # Prepare report data
            report_data = {
                "execution_metadata": {
                    "execution_id": result.execution_id,
                    "script_id": result.script_id,
                    "timestamp": result.timestamp,
                    "result": result.result,
                    "execution_time_ms": result.execution_time_ms
                },
                "terminal_response": {
                    "response_data": result.terminal_response,
                    "success": result.result == 'success',
                    "error_details": result.error_details
                },
                "operator_feedback": {
                    "notes": result.operator_notes,
                    "recommendations": self._generate_execution_recommendations(result)
                }
            }
            
            # Save execution report
            with open(report_filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created execution report: {report_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create execution report: {e}")
            return False
    
    def get_approved_scripts(self, filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get approved scripts with optional filtering.
        
        Args:
            filter_criteria: Optional filtering criteria
            
        Returns:
            List of approved scripts
        """
        try:
            scripts = []
            
            # Scan approved scripts folder
            for json_file in self.approved_path.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        script_data = json.load(f)
                    
                    # Apply filters if provided
                    if filter_criteria and not self._matches_filter(script_data, filter_criteria):
                        continue
                    
                    scripts.append(script_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to load script {json_file}: {e}")
                    continue
            
            # Sort by success rate and confidence
            scripts.sort(key=lambda x: (
                x['performance_metrics']['success_rate'],
                x['metadata']['confidence_level']
            ), reverse=True)
            
            return scripts
            
        except Exception as e:
            logger.error(f"Failed to get approved scripts: {e}")
            return []
    
    def _mask_pan(self, pan: str) -> str:
        """Mask PAN for security."""
        if len(pan) < 8:
            return 'XXXX-XXXX-XXXX-XXXX'
        return f"{pan[:4]}-XXXX-XXXX-{pan[-4:]}"
    
    def _get_geographic_region(self, country_code: str) -> str:
        """Get geographic region from country code."""
        region_mapping = {
            'US': 'North America', 'CA': 'North America', 'MX': 'North America',
            'GB': 'Europe', 'DE': 'Europe', 'FR': 'Europe', 'IT': 'Europe',
            'AU': 'Asia Pacific', 'JP': 'Asia Pacific', 'SG': 'Asia Pacific',
            'BR': 'Latin America', 'AR': 'Latin America', 'CL': 'Latin America'
        }
        return region_mapping.get(country_code, 'Unknown')
    
    def _calculate_confidence(self, success_rate: float, success_count: int) -> str:
        """Calculate confidence level based on success metrics."""
        if success_rate >= 0.9 and success_count >= 5:
            return 'very_high'
        elif success_rate >= 0.8 and success_count >= 3:
            return 'high'
        elif success_rate >= 0.6 and success_count >= 2:
            return 'medium'
        elif success_rate >= 0.4:
            return 'low'
        else:
            return 'very_low'
    
    def _determine_approval_status(self, success_rate: float, success_count: int, failure_count: int) -> str:
        """Determine approval status based on metrics."""
        if success_rate >= 0.7 and success_count >= 2 and failure_count <= success_count:
            return 'approved'
        elif success_rate >= 0.5 and success_count >= 1:
            return 'conditional'
        else:
            return 'not_approved'
    
    def _calculate_risk_score(self, payment_data: Dict[str, Any]) -> float:
        """Calculate risk score for payment."""
        risk_score = 0.0
        
        # Base risk from success rate
        success_rate = payment_data.get('success_rate', 0.0)
        risk_score += (1.0 - success_rate) * 50
        
        # Geographic risk
        country = payment_data.get('issuer_country', '')
        high_risk_countries = ['XX', 'Unknown']
        if country in high_risk_countries:
            risk_score += 20
        
        # Card type risk
        card_type = payment_data.get('card_type', '')
        if card_type.lower() in ['prepaid', 'gift']:
            risk_score += 15
        
        # Failure count impact
        failure_count = payment_data.get('failure_count', 0)
        risk_score += min(failure_count * 5, 25)
        
        return min(risk_score, 100.0)
    
    def _generate_execution_commands(self, bypass_method: str, tlv_mods: List[Dict[str, Any]], 
                                   terminal_type: str, card_brand: str) -> List[str]:
        """Generate execution commands for the script."""
        commands = []
        
        # Initialize terminal connection
        commands.append(f"# Initialize {terminal_type} terminal connection")
        commands.append("terminal.connect()")
        commands.append("terminal.authenticate()")
        
        # Card detection and reading
        commands.append("# Card detection and reading")
        commands.append("card_data = terminal.read_card()")
        commands.append(f"verify_card_brand(card_data, expected='{card_brand}')")
        
        # Apply TLV modifications
        if tlv_mods:
            commands.append("# Apply TLV modifications")
            for mod in tlv_mods:
                tag = mod.get('tag', 'Unknown')
                value = mod.get('value', '')
                commands.append(f"terminal.modify_tlv('{tag}', '{value}')")
        
        # Apply bypass method
        commands.append(f"# Apply {bypass_method} bypass method")
        if bypass_method == 'signature':
            commands.append("terminal.set_cvm('signature')")
            commands.append("terminal.disable_pin_verification()")
        elif bypass_method == 'cdcvm':
            commands.append("terminal.enable_cdcvm()")
            commands.append("terminal.set_cvm_list(['cdcvm', 'signature'])")
        elif bypass_method == 'no_cvm':
            commands.append("terminal.disable_all_cvm()")
            commands.append("terminal.set_verification_method('none')")
        
        # Execute transaction
        commands.append("# Execute transaction")
        commands.append("response = terminal.process_transaction()")
        commands.append("validate_response(response)")
        
        # Cleanup
        commands.append("# Cleanup and disconnect")
        commands.append("terminal.reset_modifications()")
        commands.append("terminal.disconnect()")
        
        return commands
    
    def _estimate_execution_time(self, bypass_method: str, tlv_count: int) -> int:
        """Estimate execution time in milliseconds."""
        base_time = 2000  # 2 seconds base
        
        # Add time for TLV modifications
        base_time += tlv_count * 200
        
        # Add time based on bypass method complexity
        method_times = {
            'signature': 500,
            'cdcvm': 800,
            'no_cvm': 300,
            'pin': 1000
        }
        base_time += method_times.get(bypass_method, 600)
        
        return base_time
    
    def _generate_tags(self, brand: str, card_type: str, bypass_method: str, 
                      approval_status: str, region: str) -> List[str]:
        """Generate tags for script categorization."""
        tags = []
        
        # Brand and type tags
        tags.append(f"brand_{brand.lower()}")
        tags.append(f"type_{card_type.lower().replace(' ', '_')}")
        
        # Method and status tags
        tags.append(f"method_{bypass_method}")
        tags.append(f"status_{approval_status}")
        
        # Geographic tag
        tags.append(f"region_{region.lower().replace(' ', '_')}")
        
        # Special tags
        if approval_status == 'approved':
            tags.append("production_ready")
        if bypass_method in ['signature', 'no_cvm']:
            tags.append("low_security")
        if bypass_method in ['pin', 'cdcvm']:
            tags.append("high_security")
        
        return tags
    
    def _generate_prerequisites(self, script: PaymentScript) -> List[str]:
        """Generate prerequisites for script execution."""
        prereqs = []
        
        prereqs.append(f"Terminal type: {script.terminal_type}")
        prereqs.append(f"Card brand: {script.card_brand}")
        prereqs.append(f"Bypass method support: {script.bypass_method}")
        
        if script.tlv_modifications:
            prereqs.append("TLV modification capability required")
        
        if script.risk_score > 50:
            prereqs.append("High-risk transaction - supervisor approval required")
        
        return prereqs
    
    def _generate_validation_steps(self, script: PaymentScript) -> List[str]:
        """Generate validation steps for script execution."""
        steps = []
        
        steps.append("Verify card detection successful")
        steps.append(f"Confirm card brand matches: {script.card_brand}")
        steps.append(f"Validate bypass method applied: {script.bypass_method}")
        
        if script.tlv_modifications:
            steps.append("Confirm all TLV modifications applied successfully")
        
        steps.append("Check transaction approval response")
        steps.append("Verify no error codes returned")
        
        return steps
    
    def _generate_rollback_commands(self, script: PaymentScript) -> List[str]:
        """Generate rollback commands in case of failure."""
        commands = []
        
        commands.append("# Emergency rollback procedures")
        commands.append("terminal.cancel_transaction()")
        commands.append("terminal.reset_all_modifications()")
        
        if script.tlv_modifications:
            commands.append("terminal.restore_original_tlv_values()")
        
        commands.append("terminal.clear_error_state()")
        commands.append("terminal.disconnect()")
        commands.append("log_failure_details()")
        
        return commands
    
    def _generate_warnings(self, script: PaymentScript) -> List[str]:
        """Generate warnings for script execution."""
        warnings = []
        
        if script.risk_score > 70:
            warnings.append("HIGH RISK: This script has elevated risk factors")
        
        if script.success_rate < 0.8:
            warnings.append("LOW SUCCESS RATE: Consider manual review")
        
        if script.bypass_method == 'no_cvm':
            warnings.append("SECURITY: No cardholder verification method")
        
        if script.failure_count > script.success_count:
            warnings.append("RELIABILITY: More failures than successes recorded")
        
        return warnings
    
    def _generate_recommendations(self, script: PaymentScript) -> List[str]:
        """Generate recommendations for script usage."""
        recommendations = []
        
        if script.confidence_level in ['very_high', 'high']:
            recommendations.append("Safe for automated execution")
        else:
            recommendations.append("Manual supervision recommended")
        
        if script.success_rate > 0.9:
            recommendations.append("Excellent performance - suitable for production")
        elif script.success_rate > 0.7:
            recommendations.append("Good performance - monitor execution")
        else:
            recommendations.append("Poor performance - consider alternative methods")
        
        return recommendations
    
    def _generate_execution_recommendations(self, result: ScriptExecution) -> List[str]:
        """Generate recommendations based on execution result."""
        recommendations = []
        
        if result.result == 'success':
            recommendations.append("Execution successful - update success metrics")
            if result.execution_time_ms < 5000:
                recommendations.append("Excellent performance time")
        elif result.result == 'failure':
            recommendations.append("Analyze failure cause and update script")
            recommendations.append("Consider alternative bypass methods")
        else:
            recommendations.append("Review error details and fix script issues")
        
        return recommendations
    
    def _matches_filter(self, script_data: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if script matches filter criteria."""
        for key, value in criteria.items():
            if key == 'card_brand':
                if script_data['card_information']['card_brand'].lower() != value.lower():
                    return False
            elif key == 'approval_status':
                if script_data['metadata']['approval_status'] != value:
                    return False
            elif key == 'min_success_rate':
                if script_data['performance_metrics']['success_rate'] < value:
                    return False
            elif key == 'bypass_method':
                if script_data['payment_method']['bypass_method'] != value:
                    return False
        
        return True
    
    def _create_database_summary(self) -> Dict[str, int]:
        """Create summary of database creation results."""
        return {
            'total_scripts': self.script_count,
            'approved_scripts': self.approved_count,
            'not_approved_scripts': self.not_approved_count,
            'approval_rate': self.approved_count / self.script_count if self.script_count > 0 else 0.0
        }


def create_automatic_databases(sqlite_path: str = "database/payments.db", 
                             output_path: str = "databases") -> Dict[str, int]:
    """
    Create automatic JSON databases from SQLite payment database.
    
    Args:
        sqlite_path: Path to source SQLite database
        output_path: Path for output databases
        
    Returns:
        Creation statistics
    """
    creator = AutomaticDatabaseCreator(output_path)
    return creator.create_databases_from_sqlite(sqlite_path)


def get_executable_scripts(approval_status: str = 'approved', 
                          filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Get executable scripts with filtering options.
    
    Args:
        approval_status: 'approved', 'not_approved', or 'all'
        filter_criteria: Optional filtering criteria
        
    Returns:
        List of executable scripts
    """
    creator = AutomaticDatabaseCreator()
    
    if approval_status == 'approved':
        return creator.get_approved_scripts(filter_criteria)
    else:
        # Implement for not_approved if needed
        return []
