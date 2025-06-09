#!/usr/bin/env python3

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

logger = logging.getLogger(__name__)

class TokenCounter:
    """Track token usage and costs for Gemini API calls"""
    
    GEMINI_PRICING = {
        "gemini-2.0-flash-exp": {
            "input_tokens_per_million": 0.075,    
            "output_tokens_per_million": 0.30,  
        },
        "gemini-1.5-pro": {
            "input_tokens_per_million": 3.50,  
            "output_tokens_per_million": 10.50, 
        },
        "gemini-1.5-flash": {
            "input_tokens_per_million": 0.075, 
            "output_tokens_per_million": 0.30, 
        }
    }
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.session_stats = {
            "start_time": datetime.now(),
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_requests": 0,
            "total_cost": 0.0,
            "requests": []
        }
        
        
        self.stats_file = "token_usage_stats.json"
        self.load_stats()
    
    def count_tokens_estimate(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation)
        For more accurate counting, you'd use the actual tokenizer
        """
        
        return len(text) // 4
    
    def log_request(self, 
                   input_text: str, 
                   output_text: str, 
                   actual_input_tokens: Optional[int] = None,
                   actual_output_tokens: Optional[int] = None,
                   request_type: str = "chat") -> Dict[str, Any]:
        """
        Log a single API request and calculate costs
        
        Args:
            input_text: The input prompt/text sent to the API
            output_text: The response text from the API
            actual_input_tokens: Actual input tokens (if available from API response)
            actual_output_tokens: Actual output tokens (if available from API response)
            request_type: Type of request (chat, completion, etc.)
        
        Returns:
            Dictionary with request stats
        """
            
        input_tokens = actual_input_tokens or self.count_tokens_estimate(input_text)
        output_tokens = actual_output_tokens or self.count_tokens_estimate(output_text)
        
     
        pricing = self.GEMINI_PRICING.get(self.model_name, self.GEMINI_PRICING["gemini-2.0-flash-exp"])
        
        input_cost = (input_tokens / 1_000_000) * pricing["input_tokens_per_million"]
        output_cost = (output_tokens / 1_000_000) * pricing["output_tokens_per_million"]
        total_cost = input_cost + output_cost
     
        request_record = {
            "timestamp": datetime.now().isoformat(),
            "request_type": request_type,
            "model": self.model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "input_text_preview": input_text[:200] + "..." if len(input_text) > 200 else input_text,
            "output_text_preview": output_text[:200] + "..." if len(output_text) > 200 else output_text
        }
        
    
        self.session_stats["total_input_tokens"] += input_tokens
        self.session_stats["total_output_tokens"] += output_tokens
        self.session_stats["total_requests"] += 1
        self.session_stats["total_cost"] += total_cost
        self.session_stats["requests"].append(request_record)
            
        logger.info(f"🔢 Token usage - Input: {input_tokens}, Output: {output_tokens}, Cost: ${total_cost:.6f}")
        
        if self.session_stats["total_requests"] % 5 == 0:  
            self.save_stats()
        
        return request_record
    
    def get_session_summary(self) -> Dict[str, Any]:
        
        duration = datetime.now() - self.session_stats["start_time"]
        
        return {
            "session_duration": str(duration),
            "total_requests": self.session_stats["total_requests"],
            "total_input_tokens": self.session_stats["total_input_tokens"],
            "total_output_tokens": self.session_stats["total_output_tokens"],
            "total_tokens": self.session_stats["total_input_tokens"] + self.session_stats["total_output_tokens"],
            "total_cost": self.session_stats["total_cost"],
            "average_cost_per_request": self.session_stats["total_cost"] / max(1, self.session_stats["total_requests"]),
            "model": self.model_name
        }
    
    def print_session_summary(self):
        
        summary = self.get_session_summary()
        
        print("\n" + "="*50)
        print("📊 TOKEN USAGE SUMMARY")
        print("="*50)
        print(f"🤖 Model: {summary['model']}")
        print(f"⏱️  Session Duration: {summary['session_duration']}")
        print(f"📞 Total Requests: {summary['total_requests']}")
        print(f"📥 Input Tokens: {summary['total_input_tokens']:,}")
        print(f"📤 Output Tokens: {summary['total_output_tokens']:,}")
        print(f"🔢 Total Tokens: {summary['total_tokens']:,}")
        print(f"💰 Total Cost: ${summary['total_cost']:.6f}")
        print(f"📊 Avg Cost/Request: ${summary['average_cost_per_request']:.6f}")
        print("="*50)
    
    def save_stats(self):
        
        try:
            
            all_stats = []
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    all_stats = json.load(f)
            
            
            session_data = self.session_stats.copy()
            session_data["start_time"] = session_data["start_time"].isoformat()
            session_data["end_time"] = datetime.now().isoformat()
            
            all_stats.append(session_data)
            
            
            if len(all_stats) > 100:
                all_stats = all_stats[-100:]
            
            
            with open(self.stats_file, 'w') as f:
                json.dump(all_stats, f, indent=2)
                
            logger.info(f"💾 Token usage stats saved to {self.stats_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving token stats: {e}")
    
    def load_stats(self):
        
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    all_stats = json.load(f)
                logger.info(f"📂 Loaded token usage history from {self.stats_file}")
            else:
                logger.info("📂 No existing token usage file found, starting fresh")
        except Exception as e:
            logger.error(f"❌ Error loading token stats: {e}")
    
    def get_total_historical_cost(self) -> float:
        
        try:
            if not os.path.exists(self.stats_file):
                return 0.0
            
            with open(self.stats_file, 'r') as f:
                all_stats = json.load(f)
            
            total_cost = sum(session.get("total_cost", 0) for session in all_stats)
            return total_cost
            
        except Exception as e:
            logger.error(f"❌ Error calculating historical cost: {e}")
            return 0.0
    
    def print_historical_summary(self):
            
        try:
            if not os.path.exists(self.stats_file):
                print("📂 No historical data available")
                return
            
            with open(self.stats_file, 'r') as f:
                all_stats = json.load(f)
            
            total_requests = sum(session.get("total_requests", 0) for session in all_stats)
            total_input_tokens = sum(session.get("total_input_tokens", 0) for session in all_stats)
            total_output_tokens = sum(session.get("total_output_tokens", 0) for session in all_stats)
            total_cost = sum(session.get("total_cost", 0) for session in all_stats)
            
            print("\n" + "="*50)
            print("📈 HISTORICAL TOKEN USAGE")
            print("="*50)
            print(f"📅 Total Sessions: {len(all_stats)}")
            print(f"📞 Total Requests: {total_requests:,}")
            print(f"📥 Total Input Tokens: {total_input_tokens:,}")
            print(f"📤 Total Output Tokens: {total_output_tokens:,}")
            print(f"🔢 Total Tokens: {(total_input_tokens + total_output_tokens):,}")
            print(f"💰 Total Historical Cost: ${total_cost:.6f}")
            print("="*50)
            
        except Exception as e:
            logger.error(f"❌ Error printing historical summary: {e}")

def create_token_counter(model_name: str = "gemini-2.0-flash-exp") -> TokenCounter:
    
    return TokenCounter(model_name)


if __name__ == "__main__":
    
    counter = TokenCounter()
    
    
    counter.log_request(
        input_text="Find me a house in New York with 3 bedrooms",
        output_text="I'll help you search for a 3-bedroom house in New York. Let me navigate to a real estate website...",
        request_type="real_estate_search"
    )
    
    counter.log_request(
        input_text="Extract the property listings from this page",
        output_text='{"listings": [{"title": "3BR House in Brooklyn", "price": "$500,000", "bedrooms": 3}]}',
        request_type="data_extraction"
    )
    
    
    counter.print_session_summary()
    counter.print_historical_summary()
    
    
    counter.save_stats() 