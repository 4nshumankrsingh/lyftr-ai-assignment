"""
Compare content across interactions to detect new content
"""
import hashlib
from typing import List, Dict, Any, Set
import logging

logger = logging.getLogger(__name__)

class ContentComparator:
    """Compare HTML content to detect changes"""
    
    def __init__(self):
        self.content_hashes = set()
        self.section_hashes = set()
    
    def add_content(self, html_content: str) -> str:
        """Add content and return hash"""
        content_hash = self._generate_hash(html_content)
        self.content_hashes.add(content_hash)
        return content_hash
    
    def add_section(self, section_text: str) -> str:
        """Add section text and return hash"""
        section_hash = self._generate_hash(section_text)
        self.section_hashes.add(section_hash)
        return section_hash
    
    def is_new_content(self, html_content: str, threshold: float = 0.3) -> bool:
        """
        Check if content is new based on similarity threshold
        
        Args:
            html_content: New HTML content to check
            threshold: Similarity threshold (0-1), lower = more strict
        
        Returns:
            True if content is sufficiently different
        """
        if not self.content_hashes:
            return True
        
        new_hash = self._generate_hash(html_content)
        
        # Check exact match first
        if new_hash in self.content_hashes:
            return False
        
        # Calculate similarity with existing content
        similarities = []
        for existing_hash in self.content_hashes:
            similarity = self._calculate_similarity(new_hash, existing_hash)
            similarities.append(similarity)
        
        if similarities:
            max_similarity = max(similarities)
            return max_similarity < (1 - threshold)
        
        return True
    
    def is_new_section(self, section_text: str, threshold: float = 0.2) -> bool:
        """Check if section is new"""
        if not self.section_hashes:
            return True
        
        new_hash = self._generate_hash(section_text)
        
        if new_hash in self.section_hashes:
            return False
        
        # Calculate similarity
        similarities = []
        for existing_hash in self.section_hashes:
            similarity = self._calculate_similarity(new_hash, existing_hash)
            similarities.append(similarity)
        
        if similarities:
            max_similarity = max(similarities)
            return max_similarity < (1 - threshold)
        
        return True
    
    def get_new_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out duplicate sections"""
        new_sections = []
        
        for section in sections:
            section_text = self._extract_section_text(section)
            if self.is_new_section(section_text):
                self.add_section(section_text)
                new_sections.append(section)
            else:
                logger.info(f"Filtered out duplicate section: {section.get('label', 'Unknown')}")
        
        return new_sections
    
    def _generate_hash(self, text: str) -> str:
        """Generate hash for text"""
        # Normalize text
        normalized = text.lower().strip()
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        # Generate hash
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _calculate_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two hashes using Hamming distance"""
        # Convert hex to binary
        bin1 = bin(int(hash1, 16))[2:].zfill(128)
        bin2 = bin(int(hash2, 16))[2:].zfill(128)
        
        # Calculate Hamming distance
        distance = sum(bit1 != bit2 for bit1, bit2 in zip(bin1, bin2))
        
        # Convert to similarity (0-1)
        similarity = 1 - (distance / 128)
        return similarity
    
    def _extract_section_text(self, section: Dict[str, Any]) -> str:
        """Extract text from section for comparison"""
        text_parts = []
        
        # Add label
        text_parts.append(section.get('label', ''))
        
        # Add headings
        content = section.get('content', {})
        text_parts.extend(content.get('headings', []))
        
        # Add main text
        text_parts.append(content.get('text', ''))
        
        # Add link texts
        for link in content.get('links', []):
            text_parts.append(link.get('text', ''))
        
        return ' '.join(text_parts)