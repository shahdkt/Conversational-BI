import time
from src.agent import app

# 50-Question Comprehensive Benchmark Suite (25 Standard + 25 Challenging)
TEST_DATASET = [
    # ==========================================
    # PART 1: 25 STANDARD BASELINE QUESTIONS
    # ==========================================
    # --- SQL Engine Standard (1-13) ---
    {"question": "Quel est le prix moyen au m² des appartements à Lyon 5e ?", "expected_route": "SQL"},
    {"question": "Combien de transactions ont été enregistrées à Villeurbanne ?", "expected_route": "SQL"},
    {"question": "Quelles sont les 5 communes les plus chères du département ?", "expected_route": "SQL"},
    {"question": "Quel est le prix moyen d'une maison vs un appartement dans le 69 ?", "expected_route": "SQL"},
    {"question": "Quel est le nombre total de ventes réalisées en 2023 ?", "expected_route": "SQL"},
    {"question": "Quelle est la valeur foncière maximale enregistrée à Caluire-et-Cuire ?", "expected_route": "SQL"},
    {"question": "Donne-moi le prix moyen au m² pour la commune de Bron.", "expected_route": "SQL"},
    {"question": "Combien de maisons de plus de 5 pièces ont été vendues à Vénissieux ?", "expected_route": "SQL"},
    {"question": "Quel est le montant total des transactions à Lyon 6e ?", "expected_route": "SQL"},
    {"question": "Affiche le nombre de ventes par type de bien dans le Rhône.", "expected_route": "SQL"},
    {"question": "Quelle est la surface réelle moyenne des maisons vendues à Meyzieu ?", "expected_route": "SQL"},
    {"question": "Combien de terrains à bâtir ont été vendus dans le département ?", "expected_route": "SQL"},
    {"question": "Quel est le prix médian des appartements à Lyon 3e ?", "expected_route": "SQL"},

    # --- Graph Engine Standard (14-25) ---
    {"question": "Trouve les appartements à Lyon 5e avec une surface > 80m².", "expected_route": "GRAPH"},
    {"question": "Quelles sont les transactions effectuées par Jean Dupont ?", "expected_route": "GRAPH"},
    {"question": "Trouve les entités ayant vendu plus de 3 biens à Lyon 5e.", "expected_route": "GRAPH"},
    {"question": "Montre-moi les appartements de plus de 3 pièces à Villeurbanne.", "expected_route": "GRAPH"},
    {"question": "Affiche les propriétés rattachées à la commune de Rillieux-la-Pape.", "expected_route": "GRAPH"},
    {"question": "Trouve les biens immobiliers achetés par la SCI Immobilier.", "expected_route": "GRAPH"},
    {"question": "Existe-t-il des maisons avec un terrain > 500m² à Décines-Charpieu ?", "expected_route": "GRAPH"},
    {"question": "Montre les entités juridiques associées aux ventes à Lyon 2e.", "expected_route": "GRAPH"},
    {"question": "Trouve les appartements de 2 pièces vendus à Givors.", "expected_route": "GRAPH"},
    {"question": "Quels biens sont enregistrés au nom de Marie Curie dans le graphe ?", "expected_route": "GRAPH"},
    {"question": "Affiche les propriétés vendues dans la section cadastrale AB.", "expected_route": "GRAPH"},
    {"question": "Trouve les entités ayant acheté un bien à la fois à Lyon et à Bron.", "expected_route": "GRAPH"},

    # ==========================================
    # PART 2: 25 CHALLENGING & EDGE CASE QUESTIONS
    # ==========================================
    # --- Advanced SQL Aggregations (26-32) ---
    {"question": "Quel est le prix au m² du 90ème percentile des appartements vendus à Villeurbanne ?", "expected_route": "SQL"},
    {"question": "Calcule la variation en pourcentage du volume de ventes entre 2022 et 2023 à Lyon 6e.", "expected_route": "SQL"},
    {"question": "Quel est le prix moyen au m² des appartements à Lyon 3e en excluant les transactions < 10 000€ et > 5 000 000€ ?", "expected_route": "SQL"},
    {"question": "Donne-moi la différence entre la médiane et la moyenne des prix pour les maisons dans le 69.", "expected_route": "SQL"},
    {"question": "Affiche le nombre de ventes et le prix moyen ventilés par type de bien et nombre de pièces à Lyon 5e.", "expected_route": "SQL"},
    {"question": "Quelles sont les 3 sections cadastrales ayant enregistré le plus grand nombre de ventes en 2023 ?", "expected_route": "SQL"},
    {"question": "Quel est le prix moyen au m² uniquement pour les appartements dont la surface Carrez est non nulle à Bron ?", "expected_route": "SQL"},

    # --- Multi-Hop Graph & Network Traversal (33-38) ---
    {"question": "Trouve les entités qui ont acheté un bien puis revendu un autre bien dans la même commune.", "expected_route": "GRAPH"},
    {"question": "Quelles sont les entités juridiques ayant acquis plus de 5 propriétés distinctes dans le département ?", "expected_route": "GRAPH"},
    {"question": "Identifie les propriétés qui ont plus d'une entité associée en tant qu'acheteur dans le graphe.", "expected_route": "GRAPH"},
    {"question": "Trouve tous les appartements rattachés à Lyon 5e avec une surface > 100m² et exactement 5 pièces.", "expected_route": "GRAPH"},
    {"question": "Montre l'écosystème complet (propriétés et municipalité) lié à l'entité 'SCI Real Estate'.", "expected_route": "GRAPH"},
    {"question": "Trouve les propriétés enregistrées dans le graphe qui ne sont reliées à aucune entité acheteuse.", "expected_route": "GRAPH"},

    # --- Ambiguous & Hybrid Routing Stress Tests (39-44) ---
    {"question": "Quel est le nombre moyen de propriétés possédées par les entités ayant acheté à Lyon 6e ?", "expected_route": "GRAPH"},
    {"question": "Trouve les appartements vendus par des entités particulières dont le prix dépasse le prix moyen de Lyon 5e.", "expected_route": "GRAPH"},
    {"question": "Quels sont les biens de plus de 3 pièces vendus à Villeurbanne avec leur prix et le nom de l'acheteur ?", "expected_route": "GRAPH"},
    {"question": "Quelle est la somme totale des transactions réalisées par les SCI dans le département ?", "expected_route": "SQL"},
    {"question": "Compare le prix moyen des ventes faites par des entreprises par rapport aux personnes physiques.", "expected_route": "SQL"},
    {"question": "Affiche les détails de la vente réalisée par la famille Martin à Bron.", "expected_route": "GRAPH"},

    # --- Edge Cases, Malformed & Out-of-Scope (45-50) ---
    {"question": "Quel temps fera-t-il demain à Lyon ?", "expected_route": "OUT_OF_SCOPE"},
    {"question": "Quel est le prix moyen à Lyon 5e ?; DROP TABLE dvf_transactions; --", "expected_route": "SQL"},
    {"question": "Donne-moi le nombre de gratte-ciels vendus à Paris 21ème arrondissement en 2025.", "expected_route": "SQL"},
    {"question": "C'est combien la maison ?", "expected_route": "CLARIFY"},
    {"question": "Quel est le prix moyen au pied carré des appartements à Lyon en dollars américains ?", "expected_route": "SQL"},
    {"question": "Affiche la couleur de la façade et la note DPE des appartements vendus à Meyzieu.", "expected_route": "SQL"}
]

def run_tests():
    print("RUNNING")
    
    correct_routes = 0
    successful_executions = 0
    total_tests = len(TEST_DATASET)
    latencies = []
    
    for idx, test in enumerate(TEST_DATASET, start=1):
        prompt = test["question"]
        expected = test["expected_route"]
        
        start_time = time.time()
        
        try:
            # Invoke LangGraph agent pipeline
            response = app.invoke({"question": prompt})
            latency = round(time.time() - start_time, 2)
            latencies.append(latency)
            
            predicted_route = response.get("route", "UNKNOWN")
            gen_query = response.get("generated_query", "")
            has_error = bool(response.get("error"))
            
            # Check 1: Intent Routing Accuracy
            route_correct = (predicted_route == expected)
            if route_correct:
                correct_routes += 1
                
            # Check 2: Execution Success (valid execution or graceful fallback handling)
            exec_ok = bool((gen_query and not has_error) or predicted_route in ["OUT_OF_SCOPE", "CLARIFY"])
            if exec_ok:
                successful_executions += 1
                
            status_route = "PASS" if route_correct else f"FAIL (Got {predicted_route})"
            status_exec = "OK" if exec_ok else "DB ERROR"
            
            print(f"[{idx:02d}/{total_tests}] Prompt: '{prompt[:42]}...'")
            print(f"       Route: {status_route} | Exec: {status_exec} | Latency: {latency}s\n")
            
        except Exception as e:
            print(f"[{idx:02d}/{total_tests}] Prompt: '{prompt[:42]}...' -> CRASHED: {e}\n")

    # Aggregate Benchmark Metrics
    routing_accuracy = (correct_routes / total_tests) * 100
    execution_rate = (successful_executions / total_tests) * 100
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print("RESULTS:")
    print(f"Total Test Questions:          {total_tests}")
    print(f"Intent Routing Accuracy:       {routing_accuracy:.1f}%")
    print(f"Query Execution Success Rate: {execution_rate:.1f}%")
    print(f"Average Pipeline Latency:     {avg_latency:.2f}s")

if __name__ == "__main__":
    run_tests()