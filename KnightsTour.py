#Copyright (c) 2009 Jacob Essex

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

import unittest, sys
import random, pygame

#Distance to look back for patterns
PATTERN_LOOKBACK = 20


class Vertex:
    """Represents a square on the board"""
    def __init__(self, x, y):
        self.edges = [] #list of edges that connect to this square
        self.x = x
        self.y = y
    
    def linksToVertex(self, v):
        """
        Returns true if this vertex has a link to v
        """
        for e in self.edges:
            if v in e.vertexes:
                return True
        return False

def linkVertexes(v1, v2):
    #TODO fix dup
    for e in v1.edges: #ensures that there isn't already a link
        if v2  in e.vertexes: 
            raise Exception("edge already exists")

    for e in v2.edges: #ensures that there isn't already a link
        if v1  in e.vertexes:
            raise Exception("edge already exists")

    e = Edge(v1, v2);
    v1.edges.append(e);
    v2.edges.append(e)
    return e
    

class TestVertex(unittest.TestCase):
    def setUp(self):
        pass
    
    def testLinksToVertex(self):
        v1 = Vertex(0,0)
        v2 = Vertex(1,2)

        linkVertexes(v1,v2)

        self.assertEqual(1, len(v1.edges))
        self.assertEqual(1, len(v2.edges))

        self.assertTrue(v1.linksToVertex(v2))
        self.assertTrue(v2.linksToVertex(v1))

class Edge:
    """Represents a edge which is in reality the neuron"""

    def __init__(self, s1, s2): 
        self.vertexes = (s1, s2)
        self.init()

    def init(self):
        """
        Separated from the constructor to allow all state to be reset
        """
        self.time = 0
        self.state = 0
        self.previousState = 0
        self.output = {0:random.randint(0,1)}

    def hasChanged(self):
        """
        Checks if the state has changed between time and time - 1
        """
        return  self.output[self.time] != self.output[self.time-1] or self.state != self.previousState


    def sumOfNeighbours(self, t):
        s = 0 
        for e in self.vertexes[0].edges + self.vertexes[1].edges:
            s += e.output[t];
        return s 

    def update(self):
        self.time += 1

        self.previousState = self.state
        self.state = self.previousState + 4 - self.sumOfNeighbours(self.time-1)

        if self.state > 3:
            self.output[self.time] = 1
        elif self.state < 0:
            self.output[self.time] = 0
        else:
            self.output[self.time] = self.output[self.time - 1]

        #stop constantly increasing memory use
        if ( len(self.output) > PATTERN_LOOKBACK ):
            del self.output[self.time-PATTERN_LOOKBACK]

class TestEdge(unittest.TestCase):
    def setUp(self):
        self.v1 = Vertex(0,1)
        self.v2 = Vertex(0,2)

        self.edge = linkVertexes(self.v1, self.v2)

    def testSumOfNeighbours(self):
        self.edge.output[0] = 0
        self.assertEqual(0, self.edge.sumOfNeighbours(0))

        self.edge.output[0] = 1 
        self.assertEqual(0, self.edge.sumOfNeighbours(0))

        v3 = Vertex(0,3)
        self.edge2 = linkVertexes(self.v2, v3)
        self.edge2.output[0] = 1
        self.assertEqual(1, self.edge.sumOfNeighbours(0))

class Board:
    def __init__(self, size):
        self.boardSize = size
        self.board = []
        self.edges = []
    
        #generates a 2d array, addressed as [x][y]  
        self.board = [[Vertex(x,y) for y in range(size)] for x in range(size)] 

    def init(self):
        """
        Separated for unit testing
        """
        for m in [(2,1), (-2,1),(1,2),(-1,2)]:
            self.addMove(m)
    

    def addMove(self, move):
        """Adds a move to all vertexes on the board"""
        mx = move[0]
        my = move[1]

        def getRange(x):
            if x >= 0: 
                return range(0,self.boardSize-x) 
            return range(abs(x), self.boardSize)

        for x in getRange(mx):
            for y in getRange(my):
                self.link((x,y), (x+mx, y+my))

    def link(self, fst, snd):
        """Links two vertexes together"""
        vfst = self.vertexAt(fst)
        vsnd = self.vertexAt(snd)
        self.edges.append(
            linkVertexes(vfst, vsnd)
        )

    def vertexIter(self):
        for x in self.board:
            for y in x:
                yield(y)
    
    def edgeIter(self):
        for e in self.edges:
            yield(e)

    def vertexAt(self, pos):
        return self.board[pos[0]][pos[1]]


    def getPossiblePatterns(self, edge, time, lookBack = range(1, PATTERN_LOOKBACK)):
        """
        Returns a set of patterns found within the edges past output, 
        optionally looking at a set of possible patterns rather than all within a range
        """
        offsets = []
        for offset in lookBack:
            if edge.output[time] == edge.output[time-offset]:
                for i in range(1, PATTERN_LOOKBACK-offset):
                    if edge.output[time-i] != edge.output[time-offset-i]:
                        break
                else: 
                    offsets.append(offset)
        return set(offsets)


    def getPatternOffsets(self, time):
        """
        Returns a set of the distances before the output of the given edges will repeat itself
        """
        if time < PATTERN_LOOKBACK or len(self.edges) == 0:
            return set([])

        patterns = self.getPossiblePatterns(self.edges[0], time)
        for edge in self.edges[1:]:
            patterns = patterns.intersection(self.getPossiblePatterns(edge,time, patterns))
        return patterns


    def reset(self):
        for n in self.edges:
            n.init()    

    def update(self):
        """
        Updates every edge by 1
        """
        for n in self.edges:
            n.update()
    
    def isStable(self):
        """
        Checks if the graph has changed since time - 1
        """
        for n in self.edges:
            if n.hasChanged():
                return False
        return True

    def isNotConvergent(self):
        """
        Checks if the neuron state changes form a patten
        """
        return len(self.getPatternOffsets(self.edges[0].time))


class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board(6)

    def hasEdge(self, fst, snd):
        return  self.board.vertexAt(fst).linksToVertex(
                self.board.vertexAt(snd)
            )

    def testAddMove(self):
        self.board.addMove((1,2))
        self.assertTrue(self.hasEdge((0,0),(1,2)))

    def testInit(self):
        self.board.init()
        self.assertTrue(self.hasEdge((0,0),(1,2)))
        self.assertTrue(self.hasEdge((5,5),(4,3)))

    def testVertexAt(self):
        self.board.init()
        self.assertEqual(0, self.board.vertexAt((0,0)).x)           
        self.assertEqual(5, self.board.vertexAt((0,5)).y)           


if __name__ == "__main__":

    #unittest.main()

    #try to give an extra speed boost
    try:
        import psyco
        psyco.full()
        print "++ using psyco ++"
    except ImportError:
        pass


    tour = Board(6)
    tour.init()

    pygame.init()
    screen = pygame.display.set_mode([tour.boardSize*50+1,tour.boardSize*50+1])
    loop = True
    numFrames = 0
    runUpdate = True

    pygame.display.set_caption("Neural Network - Knights Tour") 


    while loop:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                loop = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    loop = False
                elif event.key == pygame.K_SPACE:
                    runUpdate = False
                    tour.update()
                elif event.key == pygame.K_RETURN:
                    numFrames = 0
                    runUpdate = True
                    tour.reset()

        if runUpdate == True:
            numFrames += 1
            tour.update()

            if tour.isStable():
                runUpdate = False
                print "Knights Tour - Done : ~", numFrames,  " updates" 

            if tour.isNotConvergent():
                print "\t\tPattern Detected : ~", numFrames, " updates"
                numFrames = 0
                runUpdate = True
                hasPattern = False
                tour.reset()
        
        point = lambda x, y: (x*50+25, (tour.boardSize - 1 - y)*50+25)

        #reset the screen state to black
        screen.fill((0, 0, 0))

        #draw grid
        for i in range(tour.boardSize+2):
            pygame.draw.line(screen, (0, 255, 255), (i*50, 0), (i*50, tour.boardSize*50))
            pygame.draw.line(screen, (0, 255, 255), (0, i*50), (tour.boardSize*50, i*50))


        for n in tour.edges:
            if n.output[n.time] == 1:
                color = (0,0,255)
                pygame.draw.line(   screen,
                            color,
                            point(n.vertexes[0].x, n.vertexes[0].y),
                            point(n.vertexes[1].x, n.vertexes[1].y)
                        )

        for s in tour.vertexIter():
            pygame.draw.circle(screen, (0, 0, 255), point(s.x, s.y), 5)

        pygame.display.update()

