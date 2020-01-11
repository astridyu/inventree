from django.contrib.auth.models import User
from django.db.models import F, Sum
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from inventory.models import Item, Container, ItemTag
from inventory.serializers import ItemSerializer, ItemTagSerializer, ContainerSerializer, LoginFormSerializer, \
    UserSerializer


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)
    renderer_classes = (JSONRenderer,)
    serializer_class = LoginFormSerializer

    def post(self, request):
        user = request.data.get('user', {})

        # Notice here that we do not call `serializer.save()` like we did for
        # the registration endpoint. This is because we don't actually have
        # anything to save. Instead, the `validate` method on our serializer
        # handles everything we need.
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ItemViewSet(ModelViewSet):
    serializer_class = ItemSerializer
    parser_classes = [JSONParser]

    def get_queryset(self):
        query = Item.objects.all()

        should_filter_restock = self.request.query_params.get('needs_restock', False)
        if should_filter_restock:
            query = query.filter(quantity__lte=F('alert_quantity'))

        parent = self.request.query_params.get('parent', None)
        if parent:
            if parent == '-1':
                query = query.filter(parent__isnull=True)
            else:
                query = query.filter(parent__exact=parent)
        return query

    def create(self, request, *args, **kwargs):
        tag_names = request.data.get('tags', [])
        for tag_name in tag_names:
            ItemTag.objects.get_or_create(name=tag_name)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ContainerViewSet(ModelViewSet):
    serializer_class = ContainerSerializer
    parser_classes = [JSONParser]

    def get_queryset(self):
        query = Container.objects.all()

        parent = self.request.query_params.get('parent', None)
        if parent:
            if parent == '-1':
                query = query.filter(parent__isnull=True)
            else:
                query = query.filter(parent__exact=parent)

        return query

    @action(methods=['get'], detail=True)
    def all_parents(self, request, pk):
        container = Container.objects.get(pk=pk)
        node = container
        path = []
        while node is not None:
            path.append(node)
            node = node.parent
        serializer = ContainerSerializer(path, many=True, context={'request': request})
        return Response(serializer.data)

    @action(methods=['get'], detail=True)
    def items(self, request, pk):
        items = Item.objects.filter(parent__exact=pk)
        serializer = ItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

    @action(methods=['get'], detail=True)
    def children(self, request, pk):
        containers = Container.objects.filter(parent__exact=pk)
        serializer = ContainerSerializer(containers, many=True, context={'request': request})
        return Response(serializer.data)


class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.all()

    @action(methods=['get'], detail=False)
    def current(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)


class ItemTagViewSet(ModelViewSet):
    queryset = ItemTag.objects.all()
    serializer_class = ItemTagSerializer


class InfoView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({
            'total_item_count': Item.objects.aggregate(item_count=Sum('quantity'))['item_count'],
            'container_count': Container.objects.count()
        })


class AllParentsView(ModelViewSet):
    serializer_class = Container

    def get_queryset(self):
        node = Container.objects.get(id=self.request.query_params['id'])
        out = []
        while node is not None:
            out.append(node)
            node = node.parent
        return out

