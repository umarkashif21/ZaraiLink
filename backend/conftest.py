import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient

User = get_user_model()






@pytest.fixture
def db_access_without_rollback_and_truncate(request, django_db_setup, django_db_blocker):
    django_db_blocker.unblock()
    yield
    django_db_blocker.restore()






@pytest.fixture
def create_user(db):
    def _create_user(
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        username=None,  
        email_verified=True,
        token_balance=10,
        **kwargs
    ):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email_verified=email_verified,
            token_balance=token_balance,
            **kwargs
        )
        return user
    return _create_user


@pytest.fixture
def user(create_user):
    return create_user()


@pytest.fixture
def unverified_user(create_user):
    return create_user(
        email='unverified@example.com',
        email_verified=False
    )


@pytest.fixture
def user_no_tokens(create_user):
    return create_user(
        email='notokens@example.com',
        token_balance=0
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email='admin@example.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User'
    )






@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def authenticated_client_no_tokens(api_client, user_no_tokens):
    api_client.force_authenticate(user=user_no_tokens)
    return api_client


@pytest.fixture
def django_client():
    return Client()


@pytest.fixture
def authenticated_django_client(django_client, user):
    django_client.force_login(user)
    return django_client






@pytest.fixture
def create_sector(db):
    from companies.models import Sector

    def _create_sector(name='Agriculture', description='Agricultural products'):
        sector, _ = Sector.objects.get_or_create(
            name=name,
            defaults={'description': description}
        )
        return sector
    return _create_sector


@pytest.fixture
def create_company_role(db):
    from companies.models import CompanyRole

    def _create_role(name='Supplier', description='Product supplier'):
        role, _ = CompanyRole.objects.get_or_create(
            name=name,
            defaults={'description': description}
        )
        return role
    return _create_role


@pytest.fixture
def create_company_type(db):
    from companies.models import CompanyType

    def _create_type(name='Manufacturer', description='Manufacturing company'):
        company_type, _ = CompanyType.objects.get_or_create(
            name=name,
            defaults={'description': description}
        )
        return company_type
    return _create_type


@pytest.fixture
def create_company(db, create_sector, create_company_role, create_company_type):
    from companies.models import Company
    
    def _create_company(
        name='Test Company',
        country='Pakistan',
        verification_status='verified',
        **kwargs
    ):
        
        sector = kwargs.pop('sector', None) or create_sector()
        company_role = kwargs.pop('company_role', None) or kwargs.pop('role', None) or create_company_role()
        company_type = kwargs.pop('company_type', None) or create_company_type()
        
        company = Company.objects.create(
            name=name,
            country=country,
            verification_status=verification_status,
            sector=sector,
            company_role=company_role,
            company_type=company_type,
            **kwargs
        )
        return company
    return _create_company


@pytest.fixture
def company(create_company):
    return create_company()


@pytest.fixture
def supplier_company(create_company, create_company_role):
    supplier_role = create_company_role(name='Supplier')
    return create_company(
        name='Supplier Corp',
        role=supplier_role
    )


@pytest.fixture
def buyer_company(create_company, create_company_role):
    buyer_role = create_company_role(name='Buyer')
    return create_company(
        name='Buyer Corp',
        role=buyer_role
    )


@pytest.fixture
def create_key_contact(db, company):
    from companies.models import KeyContact
    
    def _create_contact(
        company_obj=None,
        name='John Doe',
        email='john@testcompany.com',
        phone='+92-300-1234567',
        **kwargs
    ):
        return KeyContact.objects.create(
            company=company_obj or company,
            name=name,
            email=email,
            phone=phone,
            **kwargs
        )
    return _create_contact


@pytest.fixture
def key_contact(create_key_contact):
    return create_key_contact()






@pytest.fixture
def create_subscription_plan(db):
    from subscriptions.models import SubscriptionPlan
    
    def _create_plan(
        plan_name='Basic Plan',
        price=9.99,
        tokens_included=50,
        **kwargs
    ):
        plan, _ = SubscriptionPlan.objects.get_or_create(
            plan_name=plan_name,
            defaults={
                'price': price,
                'tokens_included': tokens_included,
                'currency': 'USD',
                **kwargs
            }
        )
        return plan
    return _create_plan


@pytest.fixture
def subscription_plan(create_subscription_plan):
    return create_subscription_plan()


@pytest.fixture
def create_redeem_code(db, subscription_plan):
    from subscriptions.models import RedeemCode
    
    def _create_code(plan=None, status='active', **kwargs):
        return RedeemCode.objects.create(
            code=RedeemCode.generate_code(),
            plan=plan or subscription_plan,
            status=status,
            **kwargs
        )
    return _create_code


@pytest.fixture
def redeem_code(create_redeem_code):
    return create_redeem_code()






@pytest.fixture
def create_transaction(db, supplier_company, buyer_company):
    from trade_data.models import Transaction
    from datetime import date
    
    def _create_transaction(
        buyer=None,
        seller=None,
        hs_code='1006',
        product_description='Rice',
        quantity=1000,
        value=50000,
        **kwargs
    ):
        return Transaction.objects.create(
            buyer=buyer or buyer_company.name,
            seller=seller or supplier_company.name,
            hs_code=hs_code,
            product_description=product_description,
            quantity=quantity,
            value=value,
            reporting_date=kwargs.pop('reporting_date', date.today()),
            **kwargs
        )
    return _create_transaction






def assert_status_code(response, expected_code):
    assert response.status_code == expected_code, (
        f"Expected status code {expected_code}, got {response.status_code}. "
        f"Response: {response.content.decode()[:500]}"
    )


def assert_json_response(response):
    import json
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        pytest.fail(f"Response is not valid JSON: {response.content.decode()[:200]}")


@pytest.fixture
def assert_helpers():
    return {
        'assert_status_code': assert_status_code,
        'assert_json_response': assert_json_response,
    }
