from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UserInteraction
from utils.redis_client import RedisClient
import numpy as np
import logging

logger = logging.getLogger('zarailink')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommendations_api(request):
    """Generate recommendations based on user history"""
    user = request.user
    
    
    interactions = UserInteraction.objects.filter(user=user, action='view').select_related('company').order_by('-timestamp')[:5]
    
    if not interactions.exists():
        
        
        return Response([])
    
    
    vectors = []
    seen_ids = set()
    for i in interactions:
        vec = RedisClient.get_vector("company", i.company_id)
        if vec is not None:
            vectors.append(vec)
        seen_ids.add(str(i.company_id))
    
    if not vectors:
        return Response([])
    
    
    try:
        avg_vector = np.mean(vectors, axis=0)
    except:
        return Response([])
    
    
    results = RedisClient.search(avg_vector, top_k=10)
    
    
    recommendations = []
    for res in results:
        if res['id'] not in seen_ids:
            recommendations.append(res)
            
    return Response(recommendations)

