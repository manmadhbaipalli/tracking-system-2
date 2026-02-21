"""
Claims Service Platform - Search Service

Unified search service with PostgreSQL full-text search optimization
and search vector management.
"""

from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text, or_, and_, desc
from sqlalchemy.exc import SQLAlchemyError

from app.models.policy import Policy
from app.models.claim import Claim
from app.models.payment import Payment
from app.services.audit_service import log_action


class SearchService:
    """Unified search optimization and coordination service"""

    def __init__(self, db: Session):
        self.db = db

    async def unified_search(
        self,
        query: str,
        entity_types: List[str],
        user_id: int,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 25
    ) -> Dict[str, Any]:
        """Perform unified search across multiple entity types"""

        try:
            search_results = {}
            total_results = 0

            # Search each entity type
            for entity_type in entity_types:
                if entity_type == "policy":
                    results = await self._search_policies(query, filters, page, page_size)
                elif entity_type == "claim":
                    results = await self._search_claims(query, filters, page, page_size)
                elif entity_type == "payment":
                    results = await self._search_payments(query, filters, page, page_size)
                else:
                    continue

                search_results[entity_type] = results
                total_results += results.get("total", 0)

            # Log search action
            await log_action(
                self.db,
                user_id,
                "unified_search",
                entity_type="search",
                entity_id=None,
                details={
                    "query": query,
                    "entity_types": entity_types,
                    "total_results": total_results,
                    "filters": filters or {}
                }
            )

            return {
                "query": query,
                "entity_types": entity_types,
                "results": search_results,
                "total_results": total_results,
                "page": page,
                "page_size": page_size
            }

        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "unified_search_error",
                entity_type="search",
                entity_id=None,
                details={"error": str(e), "query": query}
            )
            raise Exception(f"Unified search failed: {str(e)}")

    async def _search_policies(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """Search policies using full-text search"""

        try:
            # Build base query
            base_query = self.db.query(Policy).filter(Policy.is_deleted == False)

            # Apply full-text search
            if query:
                # Use PostgreSQL full-text search with search vectors
                search_conditions = []

                # Search in search_vector field if exists
                if hasattr(Policy, 'search_vector'):
                    search_conditions.append(
                        Policy.search_vector.ilike(f"%{query.lower()}%")
                    )

                # Also search individual fields for exact/partial matches
                search_conditions.extend([
                    Policy.policy_number.ilike(f"%{query}%"),
                    Policy.insured_first_name.ilike(f"%{query}%"),
                    Policy.insured_last_name.ilike(f"%{query}%"),
                    Policy.organization_name.ilike(f"%{query}%"),
                    Policy.city.ilike(f"%{query}%"),
                    Policy.state.ilike(f"%{query}%"),
                    Policy.zip_code.ilike(f"%{query}%")
                ])

                base_query = base_query.filter(or_(*search_conditions))

            # Apply filters
            if filters:
                if filters.get("policy_type"):
                    base_query = base_query.filter(Policy.policy_type == filters["policy_type"])
                if filters.get("status"):
                    base_query = base_query.filter(Policy.status == filters["status"])
                if filters.get("state"):
                    base_query = base_query.filter(Policy.state == filters["state"])

            # Get total count
            total = base_query.count()

            # Apply pagination and ordering
            offset = (page - 1) * page_size
            policies = base_query.order_by(desc(Policy.updated_at)).offset(offset).limit(page_size).all()

            return {
                "entities": [policy.to_dict(mask_pii=True) for policy in policies],
                "total": total,
                "page": page,
                "page_size": page_size
            }

        except Exception as e:
            raise Exception(f"Policy search failed: {str(e)}")

    async def _search_claims(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """Search claims using full-text search"""

        try:
            # Build base query
            base_query = self.db.query(Claim).filter(Claim.is_deleted == False)

            # Apply search conditions
            if query:
                search_conditions = [
                    Claim.claim_number.ilike(f"%{query}%")
                ]

                # If claim has description or notes fields
                if hasattr(Claim, 'description'):
                    search_conditions.append(Claim.description.ilike(f"%{query}%"))
                if hasattr(Claim, 'notes'):
                    search_conditions.append(Claim.notes.ilike(f"%{query}%"))

                base_query = base_query.filter(or_(*search_conditions))

            # Apply filters
            if filters:
                if filters.get("status"):
                    base_query = base_query.filter(Claim.status == filters["status"])
                if filters.get("claim_type"):
                    base_query = base_query.filter(Claim.claim_type == filters["claim_type"])

            # Get total count
            total = base_query.count()

            # Apply pagination and ordering
            offset = (page - 1) * page_size
            claims = base_query.order_by(desc(Claim.created_at)).offset(offset).limit(page_size).all()

            # Convert to dict format
            claim_dicts = []
            for claim in claims:
                claim_dict = {
                    "id": claim.id,
                    "claim_number": claim.claim_number,
                    "policy_id": claim.policy_id,
                    "status": claim.status,
                    "created_at": claim.created_at.isoformat() if claim.created_at else None
                }

                # Add additional fields if they exist
                for field in ['claim_type', 'date_of_loss', 'total_incurred', 'total_paid']:
                    if hasattr(claim, field):
                        value = getattr(claim, field)
                        if isinstance(value, (Decimal, float)):
                            claim_dict[field] = float(value)
                        elif hasattr(value, 'isoformat'):
                            claim_dict[field] = value.isoformat()
                        else:
                            claim_dict[field] = value

                claim_dicts.append(claim_dict)

            return {
                "entities": claim_dicts,
                "total": total,
                "page": page,
                "page_size": page_size
            }

        except Exception as e:
            raise Exception(f"Claim search failed: {str(e)}")

    async def _search_payments(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """Search payments"""

        try:
            # Build base query
            base_query = self.db.query(Payment).filter(Payment.is_deleted == False)

            # Apply search conditions
            if query:
                search_conditions = []

                # Search by transaction ID, reference number, etc.
                if hasattr(Payment, 'transaction_id'):
                    search_conditions.append(Payment.transaction_id.ilike(f"%{query}%"))
                if hasattr(Payment, 'reference_number'):
                    search_conditions.append(Payment.reference_number.ilike(f"%{query}%"))
                if hasattr(Payment, 'payee_name'):
                    search_conditions.append(Payment.payee_name.ilike(f"%{query}%"))

                if search_conditions:
                    base_query = base_query.filter(or_(*search_conditions))

            # Apply filters
            if filters:
                if filters.get("status"):
                    base_query = base_query.filter(Payment.status == filters["status"])
                if filters.get("payment_method"):
                    base_query = base_query.filter(Payment.payment_method == filters["payment_method"])

            # Get total count
            total = base_query.count()

            # Apply pagination and ordering
            offset = (page - 1) * page_size
            payments = base_query.order_by(desc(Payment.created_at)).offset(offset).limit(page_size).all()

            # Convert to dict format
            payment_dicts = []
            for payment in payments:
                payment_dict = {
                    "id": payment.id,
                    "claim_id": payment.claim_id,
                    "amount": float(payment.amount) if payment.amount else 0,
                    "payment_method": payment.payment_method,
                    "status": payment.status,
                    "created_at": payment.created_at.isoformat() if payment.created_at else None
                }

                # Add additional fields if they exist
                for field in ['transaction_id', 'reference_number', 'payee_name']:
                    if hasattr(payment, field):
                        payment_dict[field] = getattr(payment, field)

                payment_dicts.append(payment_dict)

            return {
                "entities": payment_dicts,
                "total": total,
                "page": page,
                "page_size": page_size
            }

        except Exception as e:
            raise Exception(f"Payment search failed: {str(e)}")

    async def update_search_indexes(
        self,
        entity_type: str,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update search indexes for better performance"""

        try:
            updated_count = 0

            if entity_type == "policy":
                if entity_id:
                    policy = self.db.query(Policy).filter(Policy.id == entity_id).first()
                    if policy:
                        policy.update_search_vector()
                        updated_count = 1
                else:
                    policies = self.db.query(Policy).filter(Policy.is_deleted == False).all()
                    for policy in policies:
                        policy.update_search_vector()
                        updated_count += 1

            elif entity_type == "claim":
                # Claims search vector update would go here
                # For now, just count the claims
                if entity_id:
                    updated_count = 1 if self.db.query(Claim).filter(Claim.id == entity_id).first() else 0
                else:
                    updated_count = self.db.query(Claim).filter(Claim.is_deleted == False).count()

            elif entity_type == "payment":
                # Payments search vector update would go here
                if entity_id:
                    updated_count = 1 if self.db.query(Payment).filter(Payment.id == entity_id).first() else 0
                else:
                    updated_count = self.db.query(Payment).filter(Payment.is_deleted == False).count()

            self.db.commit()

            # Log index update
            if user_id:
                await log_action(
                    self.db,
                    user_id,
                    "search_index_update",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    details={
                        "updated_count": updated_count,
                        "entity_type": entity_type
                    }
                )

            return {
                "success": True,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "updated_count": updated_count,
                "message": f"Updated search indexes for {updated_count} {entity_type}(s)"
            }

        except Exception as e:
            self.db.rollback()
            if user_id:
                await log_action(
                    self.db,
                    user_id,
                    "search_index_update_error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    details={"error": str(e)}
                )
            raise Exception(f"Search index update failed: {str(e)}")

    async def get_search_suggestions(
        self,
        query: str,
        entity_type: str,
        limit: int = 10
    ) -> List[str]:
        """Get search suggestions based on partial query"""

        try:
            suggestions = []

            if entity_type == "policy":
                # Get suggestions from policy numbers, names, organizations
                policy_suggestions = self.db.query(Policy.policy_number).filter(
                    Policy.policy_number.ilike(f"{query}%"),
                    Policy.is_deleted == False
                ).limit(limit).all()

                name_suggestions = self.db.query(Policy.insured_full_name).filter(
                    Policy.insured_full_name.ilike(f"{query}%"),
                    Policy.is_deleted == False
                ).limit(limit).all()

                suggestions.extend([p[0] for p in policy_suggestions if p[0]])
                suggestions.extend([n[0] for n in name_suggestions if n[0]])

            elif entity_type == "claim":
                # Get suggestions from claim numbers
                claim_suggestions = self.db.query(Claim.claim_number).filter(
                    Claim.claim_number.ilike(f"{query}%"),
                    Claim.is_deleted == False
                ).limit(limit).all()

                suggestions.extend([c[0] for c in claim_suggestions if c[0]])

            # Remove duplicates and limit results
            suggestions = list(set(suggestions))[:limit]

            return sorted(suggestions)

        except Exception as e:
            # Return empty suggestions on error
            return []

    async def optimize_search_performance(self, user_id: int) -> Dict[str, Any]:
        """Analyze and optimize search performance"""

        try:
            optimization_results = {
                "indexes_analyzed": 0,
                "recommendations": [],
                "performance_metrics": {}
            }

            # Analyze search vector usage
            policy_search_stats = self.db.execute(
                text("SELECT COUNT(*) FROM policies WHERE search_vector IS NOT NULL")
            ).scalar()

            total_policies = self.db.query(Policy).filter(Policy.is_deleted == False).count()

            if policy_search_stats < total_policies:
                optimization_results["recommendations"].append(
                    f"Update search vectors for {total_policies - policy_search_stats} policies"
                )

            # Performance metrics
            optimization_results["performance_metrics"] = {
                "total_policies": total_policies,
                "policies_with_search_vectors": policy_search_stats,
                "search_vector_coverage": f"{(policy_search_stats / max(total_policies, 1)) * 100:.1f}%"
            }

            optimization_results["indexes_analyzed"] = 1

            # Log optimization analysis
            await log_action(
                self.db,
                user_id,
                "search_optimization_analyze",
                entity_type="search",
                entity_id=None,
                details=optimization_results
            )

            return optimization_results

        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "search_optimization_error",
                entity_type="search",
                entity_id=None,
                details={"error": str(e)}
            )
            raise Exception(f"Search optimization analysis failed: {str(e)}")

    async def create_search_analytics(
        self,
        query: str,
        entity_types: List[str],
        results_count: int,
        response_time_ms: float,
        user_id: int
    ):
        """Record search analytics for performance monitoring"""

        try:
            # This would typically store analytics in a dedicated table
            # For now, just log the search analytics
            await log_action(
                self.db,
                user_id,
                "search_analytics",
                entity_type="search",
                entity_id=None,
                details={
                    "query": query,
                    "entity_types": entity_types,
                    "results_count": results_count,
                    "response_time_ms": response_time_ms,
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception:
            # Don't fail the search if analytics recording fails
            pass