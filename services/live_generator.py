# -*- coding: utf-8 -*-
"""
services/live_generator.py
==========================
Live Generator Backend - Gamma.app-ähnlich

Features:
1. Streaming Slide Generation
2. Real-time Progress Updates
3. Slide-by-Slide Generation mit Preview
4. Interaktive Anpassung während Generierung
5. WebSocket Support vorbereitet
6. SSE (Server-Sent Events) für Live Updates

Author: StratGen Agent V3.6
"""
from __future__ import annotations
import os
import re
import json
import asyncio
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import threading
import queue

# ============================================
# CONFIGURATION
# ============================================

GENERATION_QUEUE = {}  # Active generations
MAX_CONCURRENT_GENERATIONS = 5

# ============================================
# ENUMS
# ============================================

class GenerationStatus(str, Enum):
    QUEUED = "queued"
    ANALYZING = "analyzing"
    STRUCTURING = "structuring"
    GENERATING = "generating"
    VISUALIZING = "visualizing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class SlideStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    GENERATED = "generated"
    VISUALIZING = "visualizing"
    COMPLETE = "complete"
    ERROR = "error"


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class SlideProgress:
    """Progress für einen einzelnen Slide."""
    index: int
    status: SlideStatus
    slide_type: str = ""
    title: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    preview_available: bool = False
    generation_time_ms: int = 0
    error: str = ""


@dataclass
class GenerationProgress:
    """Gesamtfortschritt einer Generierung."""
    generation_id: str
    status: GenerationStatus
    progress_percent: int
    current_phase: str
    current_slide_index: int
    total_slides: int
    slides: List[SlideProgress]
    started_at: str
    elapsed_seconds: float
    estimated_remaining_seconds: float
    messages: List[str]
    can_preview: bool
    can_edit: bool


@dataclass
class LiveGenerationRequest:
    """Request für Live-Generierung."""
    topic: str
    brief: str
    customer_name: str = ""
    industry: str = ""
    deck_size: str = "medium"
    style_profile: str = "default"
    enable_charts: bool = True
    enable_images: bool = False
    language: str = "de"


@dataclass
class SlideEdit:
    """Eine Slide-Bearbeitung während der Generierung."""
    slide_index: int
    field: str  # title, bullets, type
    new_value: Any
    regenerate: bool = False


# ============================================
# GENERATION SESSION
# ============================================

class GenerationSession:
    """
    Eine aktive Generierungs-Session.
    Verwaltet den Zustand und ermöglicht Live-Updates.
    """
    
    def __init__(self, generation_id: str, request: LiveGenerationRequest):
        self.generation_id = generation_id
        self.request = request
        self.status = GenerationStatus.QUEUED
        self.progress_percent = 0
        self.current_phase = "Initialisierung"
        self.current_slide_index = 0
        self.total_slides = 0
        self.slides: List[SlideProgress] = []
        self.started_at = datetime.now().isoformat()
        self.messages: List[str] = []
        self.event_queue = queue.Queue()
        self.cancelled = False
        self.completed_slides: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def update_status(self, status: GenerationStatus, message: str = ""):
        """Aktualisiert den Status und sendet Event."""
        with self._lock:
            self.status = status
            if message:
                self.messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
            self._send_event("status_update", {"status": status.value, "message": message})
    
    def update_progress(self, percent: int, phase: str):
        """Aktualisiert den Fortschritt."""
        with self._lock:
            self.progress_percent = percent
            self.current_phase = phase
            self._send_event("progress", {"percent": percent, "phase": phase})
    
    def start_slide(self, index: int, slide_type: str, title: str = ""):
        """Startet die Generierung eines Slides."""
        with self._lock:
            self.current_slide_index = index
            
            while len(self.slides) <= index:
                self.slides.append(SlideProgress(
                    index=len(self.slides),
                    status=SlideStatus.PENDING
                ))
            
            self.slides[index].status = SlideStatus.GENERATING
            self.slides[index].slide_type = slide_type
            self.slides[index].title = title
            
            self._send_event("slide_start", {
                "index": index,
                "type": slide_type,
                "title": title
            })
    
    def complete_slide(self, index: int, content: Dict[str, Any], generation_time_ms: int = 0):
        """Markiert einen Slide als fertig."""
        with self._lock:
            if index < len(self.slides):
                self.slides[index].status = SlideStatus.COMPLETE
                self.slides[index].content = content
                self.slides[index].preview_available = True
                self.slides[index].generation_time_ms = generation_time_ms
                self.completed_slides.append(content)
                
                self._send_event("slide_complete", {
                    "index": index,
                    "content": content,
                    "time_ms": generation_time_ms
                })
    
    def set_total_slides(self, total: int):
        """Setzt die Gesamtzahl der Slides."""
        with self._lock:
            self.total_slides = total
            self.slides = [
                SlideProgress(index=i, status=SlideStatus.PENDING)
                for i in range(total)
            ]
            self._send_event("structure", {"total_slides": total})
    
    def _send_event(self, event_type: str, data: Dict[str, Any]):
        """Sendet ein Event an die Queue."""
        self.event_queue.put({
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "generation_id": self.generation_id,
            "data": data
        })
    
    def get_progress(self) -> GenerationProgress:
        """Gibt den aktuellen Fortschritt zurück."""
        elapsed = (datetime.now() - datetime.fromisoformat(self.started_at)).total_seconds()
        
        # Geschätzte verbleibende Zeit
        if self.progress_percent > 0:
            estimated_total = elapsed / (self.progress_percent / 100)
            remaining = max(0, estimated_total - elapsed)
        else:
            remaining = 0
        
        return GenerationProgress(
            generation_id=self.generation_id,
            status=self.status,
            progress_percent=self.progress_percent,
            current_phase=self.current_phase,
            current_slide_index=self.current_slide_index,
            total_slides=self.total_slides,
            slides=self.slides.copy(),
            started_at=self.started_at,
            elapsed_seconds=round(elapsed, 1),
            estimated_remaining_seconds=round(remaining, 1),
            messages=self.messages.copy(),
            can_preview=len(self.completed_slides) > 0,
            can_edit=self.status in [GenerationStatus.GENERATING, GenerationStatus.COMPLETED]
        )
    
    def cancel(self):
        """Bricht die Generierung ab."""
        self.cancelled = True
        self.update_status(GenerationStatus.CANCELLED, "Generierung abgebrochen")
    
    def apply_edit(self, edit: SlideEdit) -> bool:
        """Wendet eine Bearbeitung auf einen Slide an."""
        with self._lock:
            if edit.slide_index >= len(self.completed_slides):
                return False
            
            slide = self.completed_slides[edit.slide_index]
            
            if edit.field == "title":
                slide["title"] = edit.new_value
            elif edit.field == "bullets":
                slide["bullets"] = edit.new_value
            elif edit.field == "type":
                slide["type"] = edit.new_value
            
            self._send_event("slide_edited", {
                "index": edit.slide_index,
                "field": edit.field,
                "new_value": edit.new_value
            })
            
            return True


# ============================================
# LIVE GENERATOR
# ============================================

class LiveGenerator:
    """
    Der Haupt-Generator für Live-Slide-Generierung.
    """
    
    def __init__(self):
        self.sessions: Dict[str, GenerationSession] = {}
    
    def create_session(self, request: LiveGenerationRequest) -> str:
        """
        Erstellt eine neue Generierungs-Session.
        
        Returns:
            generation_id
        """
        generation_id = f"live-{uuid.uuid4().hex[:12]}"
        session = GenerationSession(generation_id, request)
        self.sessions[generation_id] = session
        
        return generation_id
    
    def get_session(self, generation_id: str) -> Optional[GenerationSession]:
        """Holt eine Session."""
        return self.sessions.get(generation_id)
    
    async def generate_async(self, generation_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async Generator für Streaming-Generierung.
        Yields Events während der Generierung.
        """
        session = self.sessions.get(generation_id)
        if not session:
            yield {"type": "error", "message": "Session not found"}
            return
        
        try:
            # Phase 1: Analyse
            session.update_status(GenerationStatus.ANALYZING, "Briefing wird analysiert...")
            session.update_progress(5, "Analyse")
            yield await self._emit_event(session, "phase_start", {"phase": "analyze"})
            
            await asyncio.sleep(0.5)  # Simuliere Analyse
            
            # Briefing analysieren
            analysis = self._analyze_briefing(session.request)
            session.update_progress(15, "Analyse abgeschlossen")
            yield await self._emit_event(session, "analysis_complete", analysis)
            
            if session.cancelled:
                return
            
            # Phase 2: Struktur
            session.update_status(GenerationStatus.STRUCTURING, "Deck-Struktur wird erstellt...")
            session.update_progress(20, "Strukturierung")
            yield await self._emit_event(session, "phase_start", {"phase": "structure"})
            
            structure = self._create_structure(session.request, analysis)
            session.set_total_slides(len(structure))
            session.update_progress(25, f"Struktur: {len(structure)} Slides")
            yield await self._emit_event(session, "structure_complete", {"slides": structure})
            
            if session.cancelled:
                return
            
            # Phase 3: Slide-Generierung
            session.update_status(GenerationStatus.GENERATING, "Slides werden generiert...")
            
            for idx, slide_plan in enumerate(structure):
                if session.cancelled:
                    return
                
                # Progress berechnen
                base_progress = 25
                slide_progress = 60 * (idx + 1) / len(structure)
                session.update_progress(int(base_progress + slide_progress), f"Slide {idx + 1}/{len(structure)}")
                
                # Slide starten
                session.start_slide(idx, slide_plan["type"], slide_plan.get("title", ""))
                yield await self._emit_event(session, "slide_generating", {"index": idx})
                
                # Slide generieren
                import time
                start_time = time.time()
                
                slide_content = await self._generate_slide(session.request, slide_plan, idx)
                
                generation_time = int((time.time() - start_time) * 1000)
                
                # Slide abschließen
                session.complete_slide(idx, slide_content, generation_time)
                yield await self._emit_event(session, "slide_ready", {
                    "index": idx,
                    "slide": slide_content
                })
            
            if session.cancelled:
                return
            
            # Phase 4: Visualisierung (optional)
            if session.request.enable_charts:
                session.update_status(GenerationStatus.VISUALIZING, "Charts werden erstellt...")
                session.update_progress(90, "Visualisierung")
                yield await self._emit_event(session, "phase_start", {"phase": "visualize"})
                
                # Charts generieren
                await self._add_visualizations(session)
                yield await self._emit_event(session, "visualize_complete", {})
            
            # Phase 5: Abschluss
            session.update_status(GenerationStatus.RENDERING, "Deck wird finalisiert...")
            session.update_progress(95, "Finalisierung")
            
            # Fertig
            session.update_status(GenerationStatus.COMPLETED, "Generierung abgeschlossen!")
            session.update_progress(100, "Fertig")
            
            yield await self._emit_event(session, "complete", {
                "total_slides": len(session.completed_slides),
                "slides": session.completed_slides
            })
            
        except Exception as e:
            session.update_status(GenerationStatus.ERROR, f"Fehler: {str(e)}")
            yield await self._emit_event(session, "error", {"message": str(e)})
    
    async def _emit_event(self, session: GenerationSession, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt ein Event-Dictionary."""
        return {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "generation_id": session.generation_id,
            "progress": session.get_progress().progress_percent,
            "data": data
        }
    
    def _analyze_briefing(self, request: LiveGenerationRequest) -> Dict[str, Any]:
        """Analysiert das Briefing."""
        # Versuche Briefing Analyzer zu nutzen
        try:
            from services.briefing_analyzer import analyze
            result = analyze(request.brief, request.topic, request.industry, request.customer_name)
            return result
        except ImportError:
            pass
        
        # Fallback
        return {
            "quality_score": 70,
            "intent": "inform",
            "topics": [request.topic],
            "recommended_deck_size": request.deck_size
        }
    
    def _create_structure(self, request: LiveGenerationRequest, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Erstellt die Deck-Struktur."""
        # Versuche Story Engine zu nutzen
        try:
            from services.story_engine import create_story_structure
            story = create_story_structure(
                request.brief, request.topic,
                deck_size=request.deck_size
            )
            if story.get("ok"):
                return story.get("recommended_slides", [])
        except ImportError:
            pass
        
        # Fallback Struktur
        size_map = {"short": 5, "medium": 8, "long": 15}
        slide_count = size_map.get(request.deck_size, 8)
        
        base_structure = [
            {"type": "title", "title": request.topic},
            {"type": "executive_summary", "title": "Executive Summary"},
            {"type": "problem", "title": "Herausforderung"},
            {"type": "solution", "title": "Unser Ansatz"},
            {"type": "benefits", "title": "Ihr Nutzen"},
            {"type": "roadmap", "title": "Roadmap"},
            {"type": "roi", "title": "Business Case"},
            {"type": "next_steps", "title": "Nächste Schritte"},
            {"type": "contact", "title": "Kontakt"},
        ]
        
        return base_structure[:slide_count]
    
    async def _generate_slide(
        self,
        request: LiveGenerationRequest,
        slide_plan: Dict[str, Any],
        index: int
    ) -> Dict[str, Any]:
        """Generiert einen einzelnen Slide."""
        slide_type = slide_plan.get("type", "content")
        title = slide_plan.get("title", f"Slide {index + 1}")
        
        # LLM für Content
        try:
            from services.llm import generate as llm_generate
            
            prompt = f"""Generiere Bullet Points für einen {slide_type}-Slide:

Thema: {request.topic}
Slide-Titel: {title}
Briefing: {request.brief[:300]}
Kunde: {request.customer_name}
Branche: {request.industry}

Generiere 3-5 prägnante Bullet Points (jeweils 10-20 Wörter).

Antworte NUR mit JSON:
{{"bullets": ["Punkt 1", "Punkt 2", "Punkt 3"]}}"""
            
            result = llm_generate(prompt, max_tokens=300)
            
            if result.get("ok"):
                response = result.get("response", "")
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    bullets = data.get("bullets", [])[:5]
                    
                    return {
                        "type": slide_type,
                        "title": title,
                        "bullets": bullets,
                        "notes": f"Slide {index + 1} von {request.topic}",
                        "layout_hint": "Title and Content"
                    }
        except Exception:
            pass
        
        # Fallback
        return {
            "type": slide_type,
            "title": title,
            "bullets": [
                f"Punkt 1 zu {request.topic}",
                f"Punkt 2: Vorteile für {request.customer_name or 'den Kunden'}",
                f"Punkt 3: Umsetzung in {request.industry or 'Ihrer Branche'}",
            ],
            "notes": "",
            "layout_hint": "Title and Content"
        }
    
    async def _add_visualizations(self, session: GenerationSession):
        """Fügt Visualisierungen zu Slides hinzu."""
        try:
            from services.visual_intelligence import generate_chart_for_slide
            
            for idx, slide in enumerate(session.completed_slides):
                slide_type = slide.get("type", "")
                
                # Chart-würdige Slides
                if slide_type in ["roi", "roadmap", "kpis", "market", "competitive"]:
                    result = generate_chart_for_slide(
                        slide_type,
                        slide.get("title", ""),
                        slide.get("bullets", []),
                        {}
                    )
                    
                    if result.get("ok") and result.get("path"):
                        slide["chart"] = result["path"]
                        slide["chart_type"] = result.get("chart_type")
        except Exception:
            pass


# ============================================
# GLOBAL INSTANCE
# ============================================

live_generator = LiveGenerator()


# ============================================
# API FUNCTIONS
# ============================================

def start_generation(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Startet eine neue Live-Generierung.
    
    Args:
        request: Request-Dictionary
    
    Returns:
        Dictionary mit generation_id und Status
    """
    live_request = LiveGenerationRequest(
        topic=request.get("topic", ""),
        brief=request.get("brief", ""),
        customer_name=request.get("customer_name", ""),
        industry=request.get("industry", ""),
        deck_size=request.get("deck_size", "medium"),
        enable_charts=request.get("enable_charts", True),
        enable_images=request.get("enable_images", False)
    )
    
    generation_id = live_generator.create_session(live_request)
    
    return {
        "ok": True,
        "generation_id": generation_id,
        "status": "created",
        "stream_url": f"/live/stream/{generation_id}",
        "status_url": f"/live/status/{generation_id}"
    }


def get_generation_status(generation_id: str) -> Dict[str, Any]:
    """Gibt den Status einer Generierung zurück."""
    session = live_generator.get_session(generation_id)
    
    if not session:
        return {"ok": False, "error": "Generation not found"}
    
    progress = session.get_progress()
    
    return {
        "ok": True,
        "generation_id": generation_id,
        "status": progress.status.value,
        "progress_percent": progress.progress_percent,
        "current_phase": progress.current_phase,
        "current_slide": progress.current_slide_index,
        "total_slides": progress.total_slides,
        "elapsed_seconds": progress.elapsed_seconds,
        "estimated_remaining": progress.estimated_remaining_seconds,
        "slides_completed": len([s for s in progress.slides if s.status == SlideStatus.COMPLETE]),
        "can_preview": progress.can_preview,
        "messages": progress.messages[-5:]
    }


def get_slide_preview(generation_id: str, slide_index: int) -> Dict[str, Any]:
    """Gibt Preview eines Slides zurück."""
    session = live_generator.get_session(generation_id)
    
    if not session:
        return {"ok": False, "error": "Generation not found"}
    
    if slide_index >= len(session.completed_slides):
        return {"ok": False, "error": "Slide not yet generated"}
    
    return {
        "ok": True,
        "slide": session.completed_slides[slide_index]
    }


def edit_slide(generation_id: str, edit: Dict[str, Any]) -> Dict[str, Any]:
    """Bearbeitet einen Slide."""
    session = live_generator.get_session(generation_id)
    
    if not session:
        return {"ok": False, "error": "Generation not found"}
    
    slide_edit = SlideEdit(
        slide_index=edit.get("slide_index", 0),
        field=edit.get("field", ""),
        new_value=edit.get("new_value"),
        regenerate=edit.get("regenerate", False)
    )
    
    success = session.apply_edit(slide_edit)
    
    return {"ok": success}


def cancel_generation(generation_id: str) -> Dict[str, Any]:
    """Bricht eine Generierung ab."""
    session = live_generator.get_session(generation_id)
    
    if not session:
        return {"ok": False, "error": "Generation not found"}
    
    session.cancel()
    
    return {"ok": True, "status": "cancelled"}


def get_all_slides(generation_id: str) -> Dict[str, Any]:
    """Gibt alle generierten Slides zurück."""
    session = live_generator.get_session(generation_id)
    
    if not session:
        return {"ok": False, "error": "Generation not found"}
    
    return {
        "ok": True,
        "slides": session.completed_slides,
        "total": len(session.completed_slides)
    }


def check_status() -> Dict[str, Any]:
    """Gibt den Status des Live Generators zurück."""
    return {
        "ok": True,
        "active_sessions": len(live_generator.sessions),
        "max_concurrent": MAX_CONCURRENT_GENERATIONS,
        "features": [
            "streaming_generation",
            "real_time_progress",
            "slide_preview",
            "live_editing",
            "cancel_support"
        ]
    }
