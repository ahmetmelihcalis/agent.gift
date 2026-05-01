# agent.gift

A multi-agent gift discovery app that turns a short profile brief into personalized gift recommendations.

---

## Table of Contents / İçindekiler
- [Türkçe](#türkçe)
  - [Proje Özeti](#proje-özeti)
  - [Özellikler](#özellikler)
  - [Proje Görselleri](#proje-görselleri)
  - [Teknoloji](#teknoloji)
  - [Proje Yapısı](#proje-yapısı)
  - [Ortam Değişkenleri](#ortam-değişkenleri)
  - [Kurulum ve Çalıştırma](#kurulum-ve-çalıştırma)
  - [Nasıl Çalışır?](#nasıl-çalışır)
  - [Notlar](#notlar)
- [English](#english)
  - [Project Overview](#project-overview)
  - [Features](#features)
  - [Tech Stack](#tech-stack)
  - [Project Structure](#project-structure)
  - [Environment Variables](#environment-variables)
  - [Installation and Run](#installation-and-run)
  - [How It Works](#how-it-works)
  - [Notes](#notes)

---

# Türkçe

## Proje Özeti
`agent.gift`, kullanıcıdan alınan kısa bir profil tarifine göre kişiselleştirilmiş hediye önerileri üreten çok ajanlı çalışan bir hediye keşif uygulamasıdır.

Sistem üç temel adımda çalışır:
1. **Profili Çözümler:** Kullanıcının verdiği bilgileri analiz eder.
2. **Ürünleri Tarar:** Uygun ürünleri internet üzerinde araştırır.
3. **Derleme ve Seçim:** En güçlü önerileri seçip sadeleştirilmiş kartlar halinde sunar.

## Özellikler
- Çok Ajanlı Orkestrasyon
- Profil Analizi + Ürün Tarama + Final Değerlendirme Akışı
- SSE Tabanlı Canlı Durum Akışı
- Hata Durumlarında Fallback Aday Üretimi

## Proje Görselleri

![1](https://raw.githubusercontent.com/ahmetmelihcalis/agent.gift/refs/heads/main/images/1.jpeg)
-
![2](https://raw.githubusercontent.com/ahmetmelihcalis/agent.gift/e1cb29f3b51ce128619d61108c8cdf4acb4d0c9d/images/2.jpeg)
-
![3](https://raw.githubusercontent.com/ahmetmelihcalis/agent.gift/refs/heads/main/images/3.jpeg)
-
![4](https://raw.githubusercontent.com/ahmetmelihcalis/agent.gift/refs/heads/main/images/4.jpeg)

## Teknoloji
### Backend
- FastAPI, Pydantic, SSE Starlette
- LangChain Adaptörleri (`langchain-openai`, `langchain-tavily`)
- Tavily Search API
### Frontend
- Next.js 14, React 18, TypeScript, Tailwind CSS

## Proje Yapısı
```text
agent.gift/
├── .env
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── agents.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── services/
│   │       ├── agent_state.py
│   │       ├── crew_runner.py
│   │       ├── curation.py
│   │       ├── investigation_steps.py
│   │       ├── json_utils.py
│   │       ├── search_helpers.py
│   │       └── url_filters.py
│   └── tests/
│       └── test_health.py
├── frontend/
│   ├── app
│   ├── components
│   ├── lib
└── images/
    ├── 1.jpeg
    ├── 2.jpeg
    ├── 3.jpeg
    └── 4.jpeg
```

## Ortam Değişkenleri
Kök dizinde `.env.example` dosyasını baz alarak bir `.env` oluşturun:
```env
FAL_KEY=your_fal_key
TAVILY_API_KEY=your_tavily_key
MODEL_NAME=google/gemini-3.1-pro-preview
TAVILY_SEARCH_DEPTH=advanced
TAVILY_MAX_RESULTS=15
FRONTEND_ORIGIN=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Kurulum ve Çalıştırma

### Backend
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Nasıl Çalışır?
- **The Analyst:** Kullanıcı profilini çözümler.
- **Finder Fox:** Profile uygun ürünleri ve mağaza kaynaklarını tarar.
- **Mr. Decision:** En güçlü üç öneriyi seçer ve açıklamaları son kez düzeltir.

## Notlar
- Proje şu anda Türkiye odaklı sonuç üretmek üzere ayarlanmıştır.
- Ürün kartları doğrudan link yönlendirmesi yerine özetlenmiş bir sunum kullanır.
- Sonuç kalitesi, prompt kalitesine ve arama sonuçlarının niteliğine bağlıdır.

---

# English

## Project Overview
`agent.gift` is a multi-agent gift discovery application that generates personalized gift recommendations based on a short profile description received from the user.

The system works in three basic steps:
1. **Interprets Profile:** Analyzes the information provided by the user.
2. **Scans Products:** Researches suitable products on the internet.
3. **Compilation and Selection:** Selects the strongest recommendations and presents them as simplified cards.

## Features
- Multi-agent Orchestration
- Profile Analysis + Product Scan + Final Evaluation Flow
- SSE Based Live Status Stream
- Fallback Candidate Generation in Error Cases

## Tech Stack
### Backend
- FastAPI, Pydantic, SSE Starlette
- LangChain adapters (`langchain-openai`, `langchain-tavily`)
- Tavily Search API
### Frontend
- Next.js 14, React 18, TypeScript, Tailwind CSS

## Project Structure
```text
agent.gift/
├── .env
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── agents.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── services/
│   │       ├── agent_state.py
│   │       ├── crew_runner.py
│   │       ├── curation.py
│   │       ├── investigation_steps.py
│   │       ├── json_utils.py
│   │       ├── search_helpers.py
│   │       └── url_filters.py
│   └── tests/
│       └── test_health.py
├── frontend/
│   ├── app
│   ├── components
│   ├── lib
└── images/
    ├── 1.jpeg
    ├── 2.jpeg
    ├── 3.jpeg
    └── 4.jpeg
```

## Environment Variables
Create a `.env` file in the root directory based on the `.env.example` file:
```env
FAL_KEY=your_fal_key
TAVILY_API_KEY=your_tavily_key
MODEL_NAME=google/gemini-3.1-pro-preview
TAVILY_SEARCH_DEPTH=advanced
TAVILY_MAX_RESULTS=15
FRONTEND_ORIGIN=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Installation and Run

### Backend
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## How It Works?
- **The Analyst:** Interprets the user profile.
- **Finder Fox:** Scans products and store sources suitable for the profile.
- **Mr. Decision:** Selects the strongest three recommendations and makes final corrections to the descriptions.

## Notes
- The project is currently configured to produce Turkey-focused results.
- Product cards use a summarized presentation instead of direct link redirection.
- Result quality depends on prompt quality and the nature of search results.