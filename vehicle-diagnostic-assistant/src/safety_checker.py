"""
Safety Checker Module
Applies rule-based safety checks to vehicle data
Returns severity levels and actionable alerts
"""

from typing import Dict, List, Tuple
from enum import Enum
import config


class SeverityLevel(Enum):
    """Enumeration of safety severity levels"""
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    IMMEDIATE = "IMMEDIATE"


class SafetyChecker:
    """
    Performs rule-based safety analysis on vehicle data
    Easy to understand and justify in academic presentations
    """
    
    def __init__(self):
        """Initialize safety thresholds from config"""
        self.coolant_warning = config.COOLANT_TEMP_WARNING
        self.coolant_critical = config.COOLANT_TEMP_CRITICAL
        self.rpm_max = config.RPM_MAX_SAFE
        self.speed_max = config.SPEED_MAX_WARNING
    
    def check_all(self, vehicle_data: Dict, dtc_codes: List[tuple]) -> Dict:
        """
        Run all safety checks and return comprehensive report
        
        Args:
            vehicle_data: Dictionary containing sensor readings
            dtc_codes: List of (code, description) tuples
            
        Returns:
            Dictionary with severity, alerts, and recommendations
        """
        alerts = []
        severity = SeverityLevel.NORMAL
        
        # Check each safety condition
        temp_result = self._check_coolant_temperature(vehicle_data.get('coolant_temp'))
        rpm_result = self._check_rpm(vehicle_data.get('rpm'))
        speed_result = self._check_speed(vehicle_data.get('speed'))
        dtc_result = self._check_dtc_codes(dtc_codes)
        
        # Collect all alerts
        all_checks = [temp_result, rpm_result, speed_result, dtc_result]
        
        for check in all_checks:
            if check['alert']:
                alerts.append(check['alert'])
                # Update severity to highest level found
                if self._compare_severity(check['severity'], severity):
                    severity = check['severity']
        
        # Generate recommendations based on severity
        recommendations = self._generate_recommendations(severity, alerts)
        
        return {
            'severity': severity.value,
            'alerts': alerts,
            'recommendations': recommendations,
            'safe_to_drive': severity in [SeverityLevel.NORMAL, SeverityLevel.WARNING],
            'immediate_action_required': severity == SeverityLevel.IMMEDIATE
        }
    
    def _check_coolant_temperature(self, temp: float) -> Dict:
        """
        Rule: Check if coolant temperature is within safe range
        
        Logic:
        - temp > 120°C → CRITICAL (engine damage risk)
        - temp > 100°C → WARNING (overheating starting)
        - temp <= 100°C → NORMAL
        """
        if temp is None:
            return {'severity': SeverityLevel.NORMAL, 'alert': None}
        
        if temp > self.coolant_critical:
            return {
                'severity': SeverityLevel.IMMEDIATE,
                'alert': f"🔥 CRITICAL: Coolant temperature extremely high ({temp}°C)! Stop immediately to prevent engine damage."
            }
        elif temp > self.coolant_warning:
            return {
                'severity': SeverityLevel.CRITICAL,
                'alert': f"⚠️ WARNING: Coolant temperature high ({temp}°C). Engine may be overheating."
            }
        else:
            return {'severity': SeverityLevel.NORMAL, 'alert': None}
    
    def _check_rpm(self, rpm: float) -> Dict:
        """
        Rule: Check if RPM is within safe operating range
        
        Logic:
        - rpm > 6000 → CRITICAL (redline zone, engine stress)
        - rpm > 5000 → WARNING (high RPM sustained operation)
        - rpm <= 5000 → NORMAL
        """
        if rpm is None:
            return {'severity': SeverityLevel.NORMAL, 'alert': None}
        
        if rpm > self.rpm_max:
            return {
                'severity': SeverityLevel.CRITICAL,
                'alert': f"🔴 CRITICAL: RPM extremely high ({int(rpm)} rpm)! Reduce throttle immediately."
            }
        elif rpm > 5000:
            return {
                'severity': SeverityLevel.WARNING,
                'alert': f"⚠️ WARNING: High RPM detected ({int(rpm)} rpm). Avoid sustained high RPM."
            }
        else:
            return {'severity': SeverityLevel.NORMAL, 'alert': None}
    
    def _check_speed(self, speed: float) -> Dict:
        """
        Rule: Check if vehicle speed is safe
        
        Logic:
        - speed > 160 km/h → WARNING (very high speed)
        - speed <= 160 km/h → NORMAL
        """
        if speed is None:
            return {'severity': SeverityLevel.NORMAL, 'alert': None}
        
        if speed > self.speed_max:
            return {
                'severity': SeverityLevel.WARNING,
                'alert': f"⚠️ WARNING: High speed detected ({int(speed)} km/h). Drive within safe limits."
            }
        else:
            return {'severity': SeverityLevel.NORMAL, 'alert': None}
    
    def _check_dtc_codes(self, dtc_codes: List[tuple]) -> Dict:
        """
        Rule: Check severity of diagnostic trouble codes
        
        Logic:
        - Misfire codes (P030X) → CRITICAL (engine damage risk)
        - Catalyst codes (P0420-P0430) → WARNING (emissions issue)
        - Leak codes (P0442) → WARNING (minor issue)
        - Other codes → WARNING (requires attention)
        """
        if not dtc_codes:
            return {'severity': SeverityLevel.NORMAL, 'alert': None}
        
        critical_patterns = ['P0301', 'P0302', 'P0303', 'P0304']  # Misfire codes
        
        # Check for critical codes
        for code, description in dtc_codes:
            if code in critical_patterns:
                return {
                    'severity': SeverityLevel.CRITICAL,
                    'alert': f"🔴 CRITICAL: {code} detected - {description}. Service required soon."
                }
        
        # If no critical codes, it's a warning level issue
        code_list = ', '.join([code for code, _ in dtc_codes])
        return {
            'severity': SeverityLevel.WARNING,
            'alert': f"⚠️ WARNING: Diagnostic codes detected ({code_list}). Schedule service check."
        }
    
    def _compare_severity(self, new_severity: SeverityLevel, current_severity: SeverityLevel) -> bool:
        """
        Compare severity levels to determine which is higher
        
        Returns:
            True if new_severity is higher than current_severity
        """
        severity_order = {
            SeverityLevel.NORMAL: 0,
            SeverityLevel.WARNING: 1,
            SeverityLevel.CRITICAL: 2,
            SeverityLevel.IMMEDIATE: 3
        }
        
        return severity_order[new_severity] > severity_order[current_severity]
    
    def _generate_recommendations(self, severity: SeverityLevel, alerts: List[str]) -> List[str]:
        """
        Generate actionable recommendations based on severity level
        
        Args:
            severity: Overall severity level
            alerts: List of alert messages
            
        Returns:
            List of recommended actions
        """
        recommendations = []
        
        if severity == SeverityLevel.IMMEDIATE:
            recommendations = [
                "🛑 Pull over safely and turn off the engine immediately",
                "📞 Call for roadside assistance or towing service",
                "🚫 Do NOT continue driving to prevent serious damage",
                "🔧 Have vehicle inspected by qualified mechanic"
            ]
        
        elif severity == SeverityLevel.CRITICAL:
            recommendations = [
                "⚠️ Reduce speed and avoid aggressive driving",
                "🏠 Head to nearest service center",
                "📱 Monitor dashboard warning lights closely",
                "🔧 Schedule immediate professional inspection"
            ]
        
        elif severity == SeverityLevel.WARNING:
            recommendations = [
                "📅 Schedule service appointment within this week",
                "👀 Monitor the issue - check if it persists",
                "📖 Review owner's manual for specific guidance",
                "🔧 Consider diagnostic scan at auto parts store"
            ]
        
        else:  # NORMAL
            recommendations = [
                "✅ All systems operating normally",
                "🔄 Continue regular maintenance schedule",
                "📊 Monitor vehicle performance periodically"
            ]
        
        return recommendations
    
    def print_safety_report(self, result: Dict):
        """
        Print a formatted safety report
        
        Args:
            result: Safety check result dictionary
        """
        print("\n" + "="*60)
        print("🛡️  SAFETY ANALYSIS REPORT")
        print("="*60)
        
        # Severity indicator
        severity_emoji = {
            'NORMAL': '✅',
            'WARNING': '⚠️',
            'CRITICAL': '🔴',
            'IMMEDIATE': '🚨'
        }
        
        emoji = severity_emoji.get(result['severity'], '❓')
        print(f"\n{emoji} Overall Severity: {result['severity']}")
        print(f"{'🚗' if result['safe_to_drive'] else '🛑'} Safe to Drive: {'YES' if result['safe_to_drive'] else 'NO'}")
        
        # Alerts
        if result['alerts']:
            print("\n🔔 ALERTS:")
            for alert in result['alerts']:
                print(f"  {alert}")
        else:
            print("\n✅ No safety alerts")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "="*60 + "\n")


def main():
    """
    Demonstration of safety checker functionality
    """
    print("🛡️  Testing Safety Checker Module\n")
    
    checker = SafetyChecker()
    
    # Test Case 1: Normal conditions
    print("📋 Test Case 1: Normal Driving Conditions")
    normal_data = {
        'rpm': 2500,
        'speed': 60,
        'coolant_temp': 90,
        'engine_load': 35,
        'throttle_position': 25
    }
    normal_dtcs = []
    
    result1 = checker.check_all(normal_data, normal_dtcs)
    checker.print_safety_report(result1)
    
    # Test Case 2: High temperature warning
    print("📋 Test Case 2: High Temperature Warning")
    hot_data = {
        'rpm': 3000,
        'speed': 80,
        'coolant_temp': 115,  # HIGH!
        'engine_load': 60,
        'throttle_position': 50
    }
    result2 = checker.check_all(hot_data, normal_dtcs)
    checker.print_safety_report(result2)
    
    # Test Case 3: Critical misfire code
    print("📋 Test Case 3: Engine Misfire Detected")
    misfire_dtcs = [('P0301', 'Cylinder 1 Misfire Detected')]
    result3 = checker.check_all(normal_data, misfire_dtcs)
    checker.print_safety_report(result3)
    
    # Test Case 4: Multiple issues
    print("📋 Test Case 4: Multiple Critical Issues")
    critical_data = {
        'rpm': 6500,  # Too high!
        'speed': 170,  # Too fast!
        'coolant_temp': 125,  # Way too hot!
        'engine_load': 95,
        'throttle_position': 90
    }
    critical_dtcs = [
        ('P0301', 'Cylinder 1 Misfire'),
        ('P0420', 'Catalyst Efficiency Low')
    ]
    result4 = checker.check_all(critical_data, critical_dtcs)
    checker.print_safety_report(result4)


if __name__ == "__main__":
    main()
